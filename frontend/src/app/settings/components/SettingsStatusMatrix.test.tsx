import React from 'react';
import { render, screen } from '@testing-library/react';

import { SettingsStatusMatrix } from './SettingsStatusMatrix';

describe('SettingsStatusMatrix', () => {
    it('renders command deck cards with deterministic tags and notes', () => {
        render(
            <SettingsStatusMatrix
                cards={[
                    {
                        id: 'save',
                        title: 'Save State',
                        tone: 'warning',
                        tag: 'PENDING',
                        detail: 'Operator changes are waiting to be committed.',
                        meta: '2 local edits',
                    },
                    {
                        id: 'ollama',
                        title: 'Ollama',
                        tone: 'ready',
                        tag: 'READY',
                        detail: 'Local endpoint responded to the latest handshake.',
                    },
                ]}
            />
        );

        expect(screen.getByText('Operational Posture')).toBeInTheDocument();
        expect(screen.getByText('Save State')).toBeInTheDocument();
        expect(screen.getByText('PENDING')).toBeInTheDocument();
        expect(screen.getByText('2 local edits')).toBeInTheDocument();
        expect(screen.getByText('Ollama')).toBeInTheDocument();
        expect(screen.getByText('READY')).toBeInTheDocument();
    });
});
