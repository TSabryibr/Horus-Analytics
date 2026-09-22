import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SettingsAiProvidersSection } from './SettingsAiProvidersSection';

const settings = {
    OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
    AI_REPORT_OLLAMA_MODEL: 'qwen3-coder:30b',
    OLLAMA_API_KEY: '',
    PINE_IMPORT_TRANSLATION_PROVIDER: 'LOCAL',
};

describe('SettingsAiProvidersSection', () => {
    it('renders local Ollama controls, status messages, and wires save/test actions', () => {
        const onChange = jest.fn();
        const onSaveOllamaSettings = jest.fn();
        const onTestOllamaSettings = jest.fn();

        render(
            <SettingsAiProvidersSection
                settings={settings}
                ollamaSaving={false}
                ollamaTesting={false}
                ollamaResult={{ ok: false, message: 'Connection failed' }}
                onChange={onChange}
                onSaveOllamaSettings={onSaveOllamaSettings}
                onTestOllamaSettings={onTestOllamaSettings}
            />
        );

        fireEvent.change(screen.getByDisplayValue('http://127.0.0.1:11434'), { target: { value: 'http://localhost:11434' } });
        fireEvent.change(screen.getByPlaceholderText('qwen3-coder:30b'), { target: { value: 'qwen3.5:latest' } });
        fireEvent.change(screen.getByPlaceholderText('Optional bearer token'), { target: { value: 'token-123' } });
        fireEvent.change(screen.getByLabelText(/Pine Logic Import Translator/i), { target: { value: 'OLLAMA' } });

        fireEvent.click(screen.getByRole('button', { name: /^Save$/i }));
        fireEvent.click(screen.getByRole('button', { name: /^Test$/i }));

        expect(onChange).toHaveBeenCalledWith('OLLAMA_BASE_URL', 'http://localhost:11434');
        expect(onChange).toHaveBeenCalledWith('AI_REPORT_OLLAMA_MODEL', 'qwen3.5:latest');
        expect(onChange).toHaveBeenCalledWith('OLLAMA_API_KEY', 'token-123');
        expect(onChange).toHaveBeenCalledWith('PINE_IMPORT_TRANSLATION_PROVIDER', 'OLLAMA');
        expect(onSaveOllamaSettings).toHaveBeenCalledTimes(1);
        expect(onTestOllamaSettings).toHaveBeenCalledTimes(1);
        expect(screen.getByText('Connection failed')).toBeInTheDocument();
        expect(screen.queryByText('AI Report Provider')).not.toBeInTheDocument();
        expect(screen.getByText(/Deterministic local draft is still the default/i)).toBeInTheDocument();
    });

    it('disables save/test buttons while an Ollama action is already running', () => {
        render(
            <SettingsAiProvidersSection
                settings={settings}
                ollamaSaving={true}
                ollamaTesting={false}
                ollamaResult={null}
                onChange={jest.fn()}
                onSaveOllamaSettings={jest.fn()}
                onTestOllamaSettings={jest.fn()}
            />
        );

        expect(screen.getByRole('button', { name: /^Saving\.\.\.$/i })).toBeDisabled();
        expect(screen.getByRole('button', { name: /^Test$/i })).toBeDisabled();
    });

    it('shows an Ollama key placeholder when the backend reports a configured secret', () => {
        render(
            <SettingsAiProvidersSection
                settings={{
                    ...settings,
                    OLLAMA_API_KEY: '',
                    OLLAMA_API_KEY_CONFIGURED: true,
                    OLLAMA_API_KEY_PREVIEW: 'olla...-key',
                }}
                ollamaSaving={false}
                ollamaTesting={false}
                ollamaResult={null}
                onChange={jest.fn()}
                onSaveOllamaSettings={jest.fn()}
                onTestOllamaSettings={jest.fn()}
            />
        );

        expect(screen.getByText(/Configured: olla\.\.\.-key/i)).toBeInTheDocument();
    });
});
