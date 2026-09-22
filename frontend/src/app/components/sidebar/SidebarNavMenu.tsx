import Link from 'next/link';
import clsx from 'clsx';
import { ROUTES, TOP_NAV_ANCHORS, TOP_NAV_GROUPS } from '../config/navigation';

interface SidebarNavMenuProps {
    isCollapsed: boolean;
    pathname: string;
    t: (key: string) => string;
}

export function SidebarNavMenu({ isCollapsed, pathname, t }: SidebarNavMenuProps) {
    const isRouteActive = (href: string) =>
        href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(`${href}/`);

    const routeByHref = new Map(ROUTES.map((route) => [route.href, route]));
    const anchorRoutes = TOP_NAV_ANCHORS
        .map((href) => routeByHref.get(href))
        .filter((route): route is (typeof ROUTES)[number] => Boolean(route));
    const groupedRoutes = TOP_NAV_GROUPS.map((group) => ({
        ...group,
        routes: group.routes
            .map((href) => routeByHref.get(href))
            .filter((route): route is (typeof ROUTES)[number] => Boolean(route)),
    }));

    const renderRoute = (route: (typeof ROUTES)[number], isAnchor = false) => {
        const Icon = route.icon;
        const isActive = isRouteActive(route.href);

        return (
            <Link
                key={route.href}
                href={route.href}
                prefetch={false}
                className={clsx(
                    'group flex items-center w-full border transition-all duration-500',
                    isCollapsed ? 'justify-center rounded-[0.95rem] p-2.5' : 'mx-1 rounded-[1rem] px-3 py-2.5',
                    isAnchor && !isActive && route.href === '/'
                        ? 'border-amber-200/15 bg-[linear-gradient(135deg,rgba(38,31,19,0.72),rgba(8,10,14,0.92))]'
                        : isAnchor && !isActive
                            ? 'border-cyan-300/12 bg-[linear-gradient(135deg,rgba(10,20,25,0.75),rgba(8,10,14,0.9))]'
                            : 'border-transparent',
                    isActive
                        ? route.href === '/'
                            ? 'bg-[linear-gradient(135deg,rgba(251,191,36,0.16),rgba(120,53,15,0.18))] text-white border-amber-300/25 industrial-corner animate-in fade-in'
                            : 'bg-primary/10 text-white border-primary/30 industrial-corner animate-in fade-in'
                        : 'text-slate-500 hover:bg-white/5 hover:text-slate-200'
                )}
                title={isCollapsed ? t(route.label) : ''}
            >
                <Icon
                    className={clsx(
                        'h-4 w-4 transition-all duration-700',
                        isCollapsed ? 'mx-auto' : 'mr-4',
                        isActive
                            ? clsx('scale-110', route.color)
                            : isAnchor && route.href === '/'
                                ? 'text-amber-200/70'
                                : clsx('text-slate-600 group-hover:text-opacity-100', route.hoverColor)
                    )}
                />
                {!isCollapsed && (
                    <div className="min-w-0 flex-1">
                        <span className={clsx(
                            'block truncate text-[11px] font-black uppercase tracking-widest transition-colors',
                            isAnchor ? 'text-slate-100' : undefined
                        )}>
                            {t(route.label)}
                        </span>
                        {isAnchor ? (
                            <span className="mt-1 block truncate text-[9px] font-mono uppercase tracking-[0.24em] text-slate-500">
                                {route.href === '/' ? 'Command center' : 'Dispatch control'}
                            </span>
                        ) : null}
                    </div>
                )}
            </Link>
        );
    };

    return (
        <div className="flex-1 space-y-4">
            <div className="space-y-1">
                {!isCollapsed ? (
                    <div className="px-3 pb-1 text-[9px] font-black uppercase tracking-[0.34em] text-amber-200/60">
                        Primary
                    </div>
                ) : null}
                {anchorRoutes.map((route) => renderRoute(route, true))}
            </div>

            {groupedRoutes.map((group) => (
                <div key={group.id} className="space-y-1">
                    {!isCollapsed ? (
                        <div className="px-3 pb-1 text-[9px] font-black uppercase tracking-[0.34em] text-slate-600">
                            {group.label}
                        </div>
                    ) : null}
                    {group.routes.map((route) => renderRoute(route))}
                </div>
            ))}
        </div>
    );
}
