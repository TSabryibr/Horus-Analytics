import '@testing-library/jest-dom';
import React from 'react';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import SettingsPage from './page';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Standard backend payload returned by GET /api/v1/settings */
const BACKEND_SETTINGS = {
    LOOKBACK: 40,
    VOL_SPIKE: 2.0,
    MOMENTUM: 2.5,
    RSI_MIN: 55,
    INTRADAY_INTERVAL_MINS: 5,
    HEAT_PROTECTION_ENABLED: true,
    AUTO_TRADE_ENABLED: true,
    SIGNAL_AUTO_EXECUTION_ENABLED: true,
    LIVE_ARM_GUARD_ENABLED: false,
};

const EXCLUSIONS = ['COMI', 'HRHO'];
const TICKERS = ['COMI', 'HRHO', 'ETEL', 'SWDY', 'AMOC'];

/**
 * Build a fetch mock where each route handler can be overridden.
 * Unmatched URLs return `{ ok: true, json: {} }`.
 */
function buildFetchMock(overrides: Record<string, (init?: RequestInit) => Response | Promise<Response>> = {}) {
    return jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        for (const [pattern, handler] of Object.entries(overrides)) {
            if (url.includes(pattern)) return handler(init);
        }

        // Default route handlers
        if (url.includes('/api/v1/settings/exclusions') && (!init?.method || init.method === 'GET')) {
            return { ok: true, json: async () => EXCLUSIONS } as Response;
        }
        if (url.includes('/api/v1/settings') && (!init?.method || init.method === 'GET')) {
            return { ok: true, json: async () => ({ ...BACKEND_SETTINGS }) } as Response;
        }
        if (url.includes('/api/v1/data/tickers')) {
            return { ok: true, json: async () => TICKERS } as Response;
        }
        // POST defaults (for save tests)
        if (url.includes('/api/v1/settings') && init?.method === 'POST') {
            return { ok: true, json: async () => ({ status: 'success' }) } as Response;
        }
        if (url.includes('/api/v1/settings/exclusions') && init?.method === 'POST') {
            return { ok: true, json: async () => ({ status: 'success' }) } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
    }) as jest.Mock;
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('SettingsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        window.sessionStorage.clear();
    });

    // =======================================================================
    // 1. Initial Load
    // =======================================================================
    describe('Initial Load', () => {
        it('loads core settings and renders configuration sections', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Settings Command Deck')).toBeInTheDocument();
                expect(screen.getByText('Operational Posture')).toBeInTheDocument();
                expect(screen.getByRole('heading', { name: 'Operations & Runtime' })).toBeInTheDocument();
                expect(screen.getByText('Blacklisted Tickers')).toBeInTheDocument();
                expect(screen.getByText('Local Data Source Policy')).toBeInTheDocument();
                expect(screen.getByText('COMI')).toBeInTheDocument();
                expect(screen.getByText('HRHO')).toBeInTheDocument();
            });
        });

        it('falls back to defaults when backend is unreachable', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
            global.fetch = jest.fn(() => Promise.reject(new TypeError('Failed to fetch'))) as jest.Mock;
            render(<SettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText('Failed to load settings payload from backend.').length).toBeGreaterThan(0);
            });
            errorSpy.mockRestore();
        });

        it('handles partial failure – settings OK but exclusions fail', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
            global.fetch = buildFetchMock({
                '/api/v1/settings/exclusions': () => { throw new TypeError('Network error'); },
            });
            render(<SettingsPage />);

            await waitFor(() => {
                // Settings should still render
                expect(screen.getByText('Settings Command Deck')).toBeInTheDocument();
                // Exclusions should fall back to empty
                expect(screen.getByText('No exclusions set.')).toBeInTheDocument();
            });
            errorSpy.mockRestore();
        });

        it('silently ignores AbortError from cleanup (no error banner)', async () => {
            // Simulate an AbortError like what happens during React double-mount
            const abortError = new DOMException('The operation was aborted.', 'AbortError');
            global.fetch = jest.fn(() => Promise.reject(abortError)) as jest.Mock;

            const { unmount } = render(<SettingsPage />);
            // Unmount quickly to trigger cleanup
            unmount();

            // Re-render: fresh mount should not display the error banner from the aborted call
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Settings Command Deck')).toBeInTheDocument();
            });
            // The error from the aborted first mount should NOT show
            expect(screen.queryAllByText('Failed to load settings payload from backend.')).toHaveLength(0);
        });

        it('handles non-OK HTTP status on initial GET (e.g. 500)', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
            global.fetch = buildFetchMock({
                '/api/v1/settings': () => ({ ok: false, status: 500, statusText: 'Internal Server Error' }) as Response,
            });
            render(<SettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText('Failed to load settings payload from backend.').length).toBeGreaterThan(0);
            });
            errorSpy.mockRestore();
        });
    });

    // =======================================================================
    // 2. Exclusion Management
    // =======================================================================
    describe('Exclusion Management', () => {
        it('adds exclusion via text input and Enter key', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('COMI')).toBeInTheDocument());

            const input = screen.getByPlaceholderText('Search Ticker to Blacklist...');
            fireEvent.change(input, { target: { value: 'SWDY' } });
            fireEvent.keyDown(input, { key: 'Enter' });

            expect(screen.getByText('SWDY')).toBeInTheDocument();
        });

        it('removes exclusion via "x" button', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('COMI')).toBeInTheDocument());

            // Find the COMI chip and click its x button
            const comiChip = screen.getByText('COMI').closest('span')!;
            const removeBtn = within(comiChip).getByRole('button');
            fireEvent.click(removeBtn);

            expect(screen.queryByText('COMI')).not.toBeInTheDocument();
            // HRHO should still exist
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });

        it('ignores duplicate exclusion', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('COMI')).toBeInTheDocument());

            const input = screen.getByPlaceholderText('Search Ticker to Blacklist...');
            fireEvent.change(input, { target: { value: 'COMI' } });
            fireEvent.keyDown(input, { key: 'Enter' });

            // Should still have exactly one COMI chip
            const chips = screen.getAllByText('COMI');
            expect(chips).toHaveLength(1);
        });

        it('shows autocomplete dropdown with filtered matches', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            // Wait for tickers to load
            await waitFor(() => expect(screen.getByText('COMI')).toBeInTheDocument());

            // Type partial match
            const input = screen.getByPlaceholderText('Search Ticker to Blacklist...');
            fireEvent.change(input, { target: { value: 'ET' } });

            // ETEL should appear in dropdown (contains "ET", not excluded)
            await waitFor(() => {
                expect(screen.getByText('ETEL')).toBeInTheDocument();
            });
        });
    });

    // =======================================================================
    // 3. Form Interaction & Change Detection
    // =======================================================================
    describe('Form Interaction', () => {
        it('save button is disabled when no changes have been made', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            const saveBtn = await screen.findByRole('button', { name: /Save Changes/i });
            expect(saveBtn).toBeDisabled();
        });

        it('toggling USE_ATR_EXITS reveals ATR multiplier fields', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('Settings Command Deck')).toBeInTheDocument());

            // ATR fields should NOT be visible initially (USE_ATR_EXITS = false)
            expect(screen.queryByText('ATR TP Mult.')).not.toBeInTheDocument();

            // Find the "Use ATR Exits" label, then get the checkbox in its parent container
            const atrLabel = screen.getByText('Use ATR Exits');
            const atrContainer = atrLabel.closest('.flex.items-center.justify-between')!;
            const checkbox = within(atrContainer as HTMLElement).getByRole('checkbox');
            fireEvent.click(checkbox);

            // ATR fields should now appear
            expect(screen.getByText('ATR TP Mult.')).toBeInTheDocument();
            expect(screen.getByText('ATR SL Mult.')).toBeInTheDocument();
        });

        it('toggling AUTO_TRADE_ENABLED checkbox triggers change detection', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            const saveBtn = await screen.findByRole('button', { name: /Save Changes/i });
            expect(saveBtn).toBeDisabled();

            // Find "Auto Trading" toggle
            const autoTradeContainer = screen.getByText('Auto Trading').closest('div')!.parentElement!;
            const checkbox = within(autoTradeContainer).getByRole('checkbox');
            fireEvent.click(checkbox);

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /Save Changes/i })).toBeEnabled();
            });
        });

        it('toggling HEAT_PROTECTION_ENABLED checkbox triggers change detection', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            const saveBtn = await screen.findByRole('button', { name: /Save Changes/i });
            expect(saveBtn).toBeDisabled();

            const heatProtectionContainer = screen.getByText('Heat Protection').closest('div')!.parentElement!;
            const checkbox = within(heatProtectionContainer).getByRole('checkbox');
            fireEvent.click(checkbox);

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /Save Changes/i })).toBeEnabled();
            });
        });

        it('success message auto-clears after save', async () => {
            jest.useFakeTimers();
            const fetchMock = buildFetchMock();
            global.fetch = fetchMock;

            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('Settings Command Deck')).toBeInTheDocument());

            // Make a change to enable the save button
            const autoTradeContainer = screen.getByText('Auto Trading').closest('div')!.parentElement!;
            const checkbox = within(autoTradeContainer as HTMLElement).getByRole('checkbox');
            fireEvent.click(checkbox);

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /Save Changes/i })).toBeEnabled();
            });

            fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
            fireEvent.click(await screen.findByRole('button', { name: /Confirm & Apply Changes/i }));

            await waitFor(() => {
                expect(screen.getAllByText('Configuration Saved Successfully!').length).toBeGreaterThan(0);
            });

            // After 3 seconds the message should clear
            act(() => {
                jest.advanceTimersByTime(3000);
            });

            await waitFor(() => {
                expect(screen.queryAllByText('Configuration Saved Successfully!')).toHaveLength(0);
            });

            jest.useRealTimers();
        });
    });

    // =======================================================================
    // 4. Save
    // =======================================================================
    describe('Save', () => {
        it('saves updated settings and exclusions', async () => {
            const fetchMock = buildFetchMock();
            global.fetch = fetchMock;

            render(<SettingsPage />);

            const saveButton = await screen.findByRole('button', { name: /Save Changes/i });
            expect(saveButton).toBeDisabled();

            const momentumInput = screen.getByDisplayValue('2.5');
            fireEvent.change(momentumInput, { target: { value: '3.1' } });

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /Save Changes/i })).toBeEnabled();
            });

            fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
            fireEvent.click(await screen.findByRole('button', { name: /Confirm & Apply Changes/i }));

            await waitFor(() => {
                expect(fetchMock).toHaveBeenCalledWith(
                    expect.stringContaining('/api/v1/settings'),
                    expect.objectContaining({ method: 'POST' })
                );
                expect(screen.getAllByText('Configuration Saved Successfully!').length).toBeGreaterThan(0);
            });
        });

        it('shows save failure message when settings POST fails', async () => {
            const fetchMock = buildFetchMock({
                '/api/v1/settings': (init) => {
                    if (init?.method === 'POST') {
                        return {
                            ok: false,
                            status: 422,
                            statusText: 'Unprocessable Entity',
                            json: async () => ({ detail: 'Validation failed' }),
                        } as unknown as Response;
                    }
                    return { ok: true, json: async () => ({ ...BACKEND_SETTINGS }) } as Response;
                },
            });
            global.fetch = fetchMock;

            render(<SettingsPage />);

            const momentumInput = await screen.findByDisplayValue('2.5');
            fireEvent.change(momentumInput, { target: { value: '3.4' } });
            fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
            fireEvent.click(await screen.findByRole('button', { name: /Confirm & Apply Changes/i }));

            await waitFor(() => {
                expect(screen.getByText(/Failed to save settings: Validation failed/i)).toBeInTheDocument();
            });
        });

        it('shows "Network Error." when fetch throws during save', async () => {
            // Load normally first
            const normalFetch = buildFetchMock();
            global.fetch = normalFetch;
            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('Settings Command Deck')).toBeInTheDocument());

            const momentumInput = screen.getByDisplayValue('2.5');
            fireEvent.change(momentumInput, { target: { value: '9.9' } });

            // Now make POST throw a network error
            global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
                if (init?.method === 'POST') throw new TypeError('Failed to fetch');
                return normalFetch(input, init);
            }) as jest.Mock;

            fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
            fireEvent.click(await screen.findByRole('button', { name: /Confirm & Apply Changes/i }));

            await waitFor(() => {
                expect(screen.getByText('Network Error.')).toBeInTheDocument();
            });
        });

        it('shows failure when exclusions POST fails but settings POST succeeds', async () => {
            const fetchMock = buildFetchMock({
                '/api/v1/settings/exclusions': (init) => {
                    if (init?.method === 'POST') {
                        return {
                            ok: false,
                            status: 500,
                            statusText: 'Server Error',
                            json: async () => ({ message: 'DB write failed' }),
                        } as unknown as Response;
                    }
                    return { ok: true, json: async () => EXCLUSIONS } as Response;
                },
            });
            global.fetch = fetchMock;

            render(<SettingsPage />);

            const momentumInput = await screen.findByDisplayValue('2.5');
            fireEvent.change(momentumInput, { target: { value: '4.0' } });
            fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
            fireEvent.click(await screen.findByRole('button', { name: /Confirm & Apply Changes/i }));

            await waitFor(() => {
                expect(screen.getByText(/Failed to save settings/i)).toBeInTheDocument();
            });
        });

        it('parses error from "message" key when "detail" is absent', async () => {
            const fetchMock = buildFetchMock({
                '/api/v1/settings': (init) => {
                    if (init?.method === 'POST') {
                        return {
                            ok: false,
                            status: 400,
                            statusText: 'Bad Request',
                            json: async () => ({ message: 'Invalid parameters' }),
                        } as unknown as Response;
                    }
                    return { ok: true, json: async () => ({ ...BACKEND_SETTINGS }) } as Response;
                },
            });
            global.fetch = fetchMock;

            render(<SettingsPage />);

            const momentumInput = await screen.findByDisplayValue('2.5');
            fireEvent.change(momentumInput, { target: { value: '7.7' } });
            fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
            fireEvent.click(await screen.findByRole('button', { name: /Confirm & Apply Changes/i }));

            await waitFor(() => {
                expect(screen.getByText(/Failed to save settings: Invalid parameters/i)).toBeInTheDocument();
            });
        });
    });

    // =======================================================================
    // 5. Telegram Test Button
    // =======================================================================
    describe('Telegram Test', () => {
        it('sends test alert and shows success message', async () => {
            const fetchMock = buildFetchMock({
                '/api/v1/alerts/test': () => ({
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        target_chat_id: '-100123',
                        message: 'Primary Telegram test sent to -100123.',
                    }),
                }) as Response,
            });
            global.fetch = fetchMock;

            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('Settings Command Deck')).toBeInTheDocument());

            const testBtn = screen.getByRole('button', { name: /Test Main Channel/i });
            fireEvent.click(testBtn);

            await waitFor(() => {
                expect(fetchMock).toHaveBeenCalledWith(
                    expect.stringContaining('/api/v1/alerts/test'),
                    expect.objectContaining({ method: 'POST' })
                );
                expect(screen.getAllByText('Primary Telegram test sent to -100123.').length).toBeGreaterThan(0);
            });
        });

        it('shows "Test Failed" when test alert fetch throws', async () => {
            const fetchMock = buildFetchMock({
                '/api/v1/alerts/test': () => { throw new TypeError('Network error'); },
            });
            global.fetch = fetchMock;

            render(<SettingsPage />);

            await waitFor(() => expect(screen.getByText('Settings Command Deck')).toBeInTheDocument());

            const testBtn = screen.getByRole('button', { name: /Test Main Channel/i });
            fireEvent.click(testBtn);

            await waitFor(() => {
                expect(screen.getAllByText('Test Failed').length).toBeGreaterThan(0);
            });
        });
    });

    // =======================================================================
    // 6. Market Hour Offsets
    // =======================================================================
    describe('Market Hour Offsets', () => {
        it('renders the new offset and interval fields with correct values', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Market Hours')).toBeInTheDocument();
            });

            // Check if fields are rendered with values from BACKEND_SETTINGS
            expect(screen.getByLabelText(/Pre-Close Offset/i)).toHaveValue(20);
            expect(screen.getByLabelText(/Daily Signal Offset/i)).toHaveValue(30);
            expect(screen.getByLabelText(/Intraday Interval/i)).toHaveValue(5);
        });

        it('triggers change detection when market hour offsets are modified', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            const saveBtn = await screen.findByRole('button', { name: /Save Changes/i });
            expect(saveBtn).toBeDisabled();

            const preCloseInput = screen.getByLabelText(/Pre-Close Offset/i);
            fireEvent.change(preCloseInput, { target: { value: '25' } });

            await waitFor(() => {
                expect(saveBtn).toBeEnabled();
            });
        });

        it('renders command deck status cards, jump rail, and missing strategy fields in the reorganized layout', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Save State')).toBeInTheDocument();
                expect(screen.getAllByText('Execution Gate').length).toBeGreaterThan(0);
                expect(screen.getAllByText('AUTO_ENTRY').length).toBeGreaterThan(0);
                expect(screen.getByText('Ollama')).toBeInTheDocument();
                expect(screen.getByRole('heading', { name: 'Delivery & AI' })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /Jump to Strategy & Risk/i })).toBeInTheDocument();
                expect(screen.getAllByRole('link', { name: /Operations & Runtime/i }).length).toBeGreaterThan(0);
                expect(screen.getAllByRole('link', { name: /Strategy & Risk/i }).length).toBeGreaterThan(0);
                expect(screen.getByLabelText(/Signal Lookback/i)).toHaveValue(40);
                expect(screen.getByText('Min Signal Score')).toBeInTheDocument();
                expect(screen.getByText('Max Portfolio Heat %')).toBeInTheDocument();
                expect(screen.getByLabelText('Intraday dispatch')).toBeChecked();
                expect(screen.getByLabelText('Daily dispatch')).toBeChecked();
            });
        });
    });

    // =======================================================================
    // 7. Hotkey Navigation
    // =======================================================================
    describe('Hotkey Navigation', () => {
        it('opens diff modal when Ctrl+S is pressed with pending changes', async () => {
            global.fetch = buildFetchMock();
            render(<SettingsPage />);

            const momentumInput = await screen.findByDisplayValue('2.5');
            fireEvent.change(momentumInput, { target: { value: '3.9' } });

            fireEvent.keyDown(window, { key: 's', ctrlKey: true });

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /Confirm & Apply Changes/i })).toBeInTheDocument();
            });
        });
    });
});
