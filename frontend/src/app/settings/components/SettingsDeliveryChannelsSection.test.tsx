import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SettingsDeliveryChannelsSection } from './SettingsDeliveryChannelsSection';

const settings = {
    TELEGRAM_TOKEN: 'token',
    CHAT_ID: '-100123',
    TELEGRAM_AUTO_BROADCAST_INTRADAY: true,
    TELEGRAM_AUTO_BROADCAST_DAILY: true,
    TELEGRAM_AUTO_BROADCAST_HORUS_EYE: false,
    TELEGRAM_AUTO_BROADCAST_AI_REPORT: true,
    TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT: false,
    TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT: false,
    TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL: 'type_1',
    TELEGRAM_REPORT_LANGUAGE: 'EN',
    WEBHOOK_ENABLED: true,
    WEBHOOK_URL: 'https://example.com/hook',
};

const signalDeskPolicy = {
    operatingMode: 'AI_ASSIST' as const,
    autopilotArmed: true,
    confidenceFloor: 76,
    minCandidates: 2,
    sourceModules: ['SCANNER', 'ORACLE'],
    signalTypes: ['INTRADAY', 'SWING'],
};

describe('SettingsDeliveryChannelsSection', () => {
    it('renders telegram and webhook controls and wires change/save/test handlers', () => {
        const onChange = jest.fn();
        const onSignalDeskPolicyChange = jest.fn();
        const onSaveTelegramConfig = jest.fn();
        const onSendTelegramTest = jest.fn();
        const onTestWebhook = jest.fn();

        render(
            <SettingsDeliveryChannelsSection
                settings={settings}
                signalDeskPolicy={signalDeskPolicy}
                saving={false}
                telegramResult={{ ok: true, message: 'Telegram route armed.' }}
                testBotResult={null}
                webhookResult={{ ok: false, message: 'Webhook probe failed.' }}
                onChange={onChange}
                onSignalDeskPolicyChange={onSignalDeskPolicyChange}
                onSaveTelegramConfig={onSaveTelegramConfig}
                onSendTelegramTest={onSendTelegramTest}
                onSaveTestTelegramConfig={jest.fn()}
                onSendTestTelegramBotTest={jest.fn()}
                onTestWebhook={onTestWebhook}
            />
        );

        fireEvent.change(screen.getByPlaceholderText('123456:ABC-DEF...'), { target: { value: 'updated-token' } });
        fireEvent.change(screen.getByLabelText('Premium Signal Channel ID'), { target: { value: '-100999' } });
        fireEvent.click(screen.getByLabelText('Intraday dispatch'));
        fireEvent.change(screen.getByLabelText('Automated signal channel level'), { target: { value: 'type_2' } });
        fireEvent.change(screen.getByLabelText('Telegram report language'), { target: { value: 'AR' } });
        fireEvent.click(screen.getByRole('button', { name: /Autopilot/i }));
        fireEvent.click(screen.getByLabelText('Autopilot armed'));
        fireEvent.change(screen.getByLabelText('Confidence Floor'), { target: { value: '88' } });
        fireEvent.click(screen.getByRole('checkbox', { name: /Webhook enabled/i }));
        fireEvent.change(screen.getByPlaceholderText('https://your-api.com/webhooks/horus'), { target: { value: 'https://hook.example' } });

        fireEvent.click(screen.getByRole('button', { name: /^Save$/i }));
        fireEvent.click(screen.getByRole('button', { name: /Test Main Channel/i }));
        fireEvent.click(screen.getByRole('button', { name: /Test Webhook/i }));

        expect(screen.getByText(/Main Type 1 signal channel/i)).toBeInTheDocument();
        expect(screen.getByText(/Subscriber private tests run from the Subscribers console/i)).toBeInTheDocument();
        expect(onChange).toHaveBeenCalledWith('TELEGRAM_TOKEN', 'updated-token');
        expect(onChange).toHaveBeenCalledWith('CHAT_ID', '-100999');
        expect(onChange).toHaveBeenCalledWith('TELEGRAM_AUTO_BROADCAST_INTRADAY', false);
        expect(onChange).toHaveBeenCalledWith('TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL', 'type_2');
        expect(onChange).toHaveBeenCalledWith('TELEGRAM_REPORT_LANGUAGE', 'AR');
        expect(onChange).toHaveBeenCalledWith('WEBHOOK_ENABLED', false);
        expect(onChange).toHaveBeenCalledWith('WEBHOOK_URL', 'https://hook.example');
        expect(onSignalDeskPolicyChange).toHaveBeenCalledWith('operatingMode', 'AUTOPILOT');
        expect(onSignalDeskPolicyChange).toHaveBeenCalledWith('autopilotArmed', false);
        expect(onSignalDeskPolicyChange).toHaveBeenCalledWith('confidenceFloor', 88);
        expect(onSaveTelegramConfig).toHaveBeenCalled();
        expect(onSendTelegramTest).toHaveBeenCalled();
        expect(onTestWebhook).toHaveBeenCalled();
        expect(screen.getByText('Telegram route armed.')).toBeInTheDocument();
        expect(screen.getByText('Webhook probe failed.')).toBeInTheDocument();
    });

    it('disables webhook testing when no webhook url exists or a save is in progress', () => {
        const { rerender } = render(
            <SettingsDeliveryChannelsSection
                settings={{ ...settings, WEBHOOK_URL: '' }}
                signalDeskPolicy={signalDeskPolicy}
                saving={false}
                telegramResult={null}
                testBotResult={null}
                webhookResult={null}
                onChange={jest.fn()}
                onSignalDeskPolicyChange={jest.fn()}
                onSaveTelegramConfig={jest.fn()}
                onSendTelegramTest={jest.fn()}
                onSaveTestTelegramConfig={jest.fn()}
                onSendTestTelegramBotTest={jest.fn()}
                onTestWebhook={jest.fn()}
            />
        );

        expect(screen.getByRole('button', { name: /Test Webhook/i })).toBeDisabled();

        rerender(
            <SettingsDeliveryChannelsSection
                settings={settings}
                signalDeskPolicy={signalDeskPolicy}
                saving={true}
                telegramResult={null}
                testBotResult={null}
                webhookResult={null}
                onChange={jest.fn()}
                onSignalDeskPolicyChange={jest.fn()}
                onSaveTelegramConfig={jest.fn()}
                onSendTelegramTest={jest.fn()}
                onSaveTestTelegramConfig={jest.fn()}
                onSendTestTelegramBotTest={jest.fn()}
                onTestWebhook={jest.fn()}
            />
        );

        expect(screen.getByRole('button', { name: /Test Webhook/i })).toBeDisabled();
    });

    it('shows configured credential placeholders without exposing stored secrets', () => {
        render(
            <SettingsDeliveryChannelsSection
                settings={{
                    ...settings,
                    TELEGRAM_TOKEN: '',
                    TELEGRAM_TOKEN_CONFIGURED: true,
                    TELEGRAM_TOKEN_PREVIEW: '1234...7890',
                    CHAT_ID: '',
                    CHAT_ID_CONFIGURED: true,
                    CHAT_ID_PREVIEW: '-100...1234',
                    TELEGRAM_TEST_BOT_TOKEN: '',
                    TELEGRAM_TEST_BOT_TOKEN_CONFIGURED: true,
                    TELEGRAM_TEST_BOT_TOKEN_PREVIEW: '9876...4321',
                    TELEGRAM_TEST_CHAT_ID: '',
                    TELEGRAM_TEST_CHAT_ID_CONFIGURED: true,
                    TELEGRAM_TEST_CHAT_ID_PREVIEW: '-100...9999',
                }}
                signalDeskPolicy={signalDeskPolicy}
                saving={false}
                telegramResult={null}
                testBotResult={null}
                webhookResult={null}
                onChange={jest.fn()}
                onSignalDeskPolicyChange={jest.fn()}
                onSaveTelegramConfig={jest.fn()}
                onSendTelegramTest={jest.fn()}
                onSaveTestTelegramConfig={jest.fn()}
                onSendTestTelegramBotTest={jest.fn()}
                onTestWebhook={jest.fn()}
            />
        );

        expect(screen.getByText(/Configured: 1234\.\.\.7890/i)).toBeInTheDocument();
        expect(screen.getByText(/Configured: -100\.\.\.1234/i)).toBeInTheDocument();
        expect(screen.getByText(/Configured: 9876\.\.\.4321/i)).toBeInTheDocument();
        expect(screen.getByText(/Configured: -100\.\.\.9999/i)).toBeInTheDocument();
    });
});
