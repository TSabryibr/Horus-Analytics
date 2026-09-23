describe('resolveApiOrigin', () => {
    it('prefers the current loopback host when the configured API URL differs only by localhost vs 127.0.0.1 on the same port', async () => {
        const api = await import('./api');

        expect(api.resolveApiOrigin('http://localhost:8000', 'http://127.0.0.1:8000')).toBe('http://127.0.0.1:8000');
        expect(api.resolveApiOrigin('http://127.0.0.1:8000', 'http://localhost:8000')).toBe('http://localhost:8000');
    });

    it('keeps the configured API URL when the current origin is on a different port', async () => {
        const api = await import('./api');

        expect(api.resolveApiOrigin('http://localhost:8000', 'http://127.0.0.1:3000')).toBe('http://localhost:8000');
    });

    it('falls back to the backend dev origin when running on a local frontend dev port without a configured API URL', async () => {
        const api = await import('./api');

        expect(api.resolveApiOrigin(undefined, 'http://localhost:3000')).toBe('http://localhost:8100');
        expect(api.resolveApiOrigin(undefined, 'http://127.0.0.1:3100')).toBe('http://localhost:8100');
    });

    it('falls back to the current origin outside the local frontend dev port pattern when no configured API URL is provided', async () => {
        const api = await import('./api');

        expect(api.resolveApiOrigin(undefined, 'http://127.0.0.1:8000')).toBe('http://127.0.0.1:8000');
        expect(api.resolveApiOrigin(undefined, 'https://horus.example')).toBe('https://horus.example');
    });
});
