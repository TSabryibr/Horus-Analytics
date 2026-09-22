import { render, screen } from '@testing-library/react';

import { ROUTES, TOP_NAV_ANCHORS, TOP_NAV_GROUPS } from '@/app/components/config/navigation';
import { LanguageProvider, useLanguage } from './LanguageContext';

function NavigationTranslationProbe() {
    const { t } = useLanguage();
    const routeByHref = new Map(ROUTES.map((route) => [route.href, route]));
    const navigationHrefs = [
        ...TOP_NAV_ANCHORS,
        ...TOP_NAV_GROUPS.flatMap((group) => group.routes),
    ];
    const labels = navigationHrefs
        .map((href) => routeByHref.get(href)?.label)
        .filter((label): label is string => Boolean(label));
    const missingLabels = labels
        .map((label) => t(label))
        .filter((label) => label.startsWith('nav.'));

    return <div data-testid="missing-navigation-labels">{missingLabels.join(',')}</div>;
}

describe('LanguageProvider navigation labels', () => {
    beforeEach(() => {
        window.localStorage.clear();
    });

    it('resolves every top navigation chamber route to a real display label', () => {
        render(
            <LanguageProvider>
                <NavigationTranslationProbe />
            </LanguageProvider>
        );

        expect(screen.getByTestId('missing-navigation-labels')).toBeEmptyDOMElement();
    });
});
