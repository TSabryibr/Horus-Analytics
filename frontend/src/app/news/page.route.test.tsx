import React from 'react';
import { render, screen } from '@testing-library/react';
import NewsPage from './page';
import { apiFetch } from '@/lib/api';

jest.mock('@/lib/api', () => ({
    apiFetch: jest.fn(),
    readJsonSafe: jest.fn(),
}));

jest.mock('./NewsClient', () => function MockNewsClient() {
    return <div>News Client</div>;
});

describe('NewsPage route', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders the page directly without nesting another global data provider', async () => {
        const page = await Promise.resolve(NewsPage());
        render(page);

        expect(screen.getByText('News Client')).toBeInTheDocument();
        expect(apiFetch).not.toHaveBeenCalled();
    });
});
