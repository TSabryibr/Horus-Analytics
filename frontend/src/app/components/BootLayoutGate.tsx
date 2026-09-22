'use client';

import React, { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

import SystemBootOverlay from './SystemBootOverlay';
import { SYSTEM_BOOT_SESSION_KEY } from './systemBootModel';

interface BootLayoutGateProps {
    children: React.ReactNode;
}

export default function BootLayoutGate({ children }: BootLayoutGateProps) {
    const pathname = usePathname();
    const isHomeRoute = pathname === '/';
    const [isStartupReady, setIsStartupReady] = useState(!isHomeRoute);

    useEffect(() => {
        if (!isHomeRoute) {
            setIsStartupReady(true);
            return;
        }

        const sessionBooted = window.sessionStorage.getItem(SYSTEM_BOOT_SESSION_KEY);
        setIsStartupReady(Boolean(sessionBooted));
    }, [isHomeRoute]);

    if (!isHomeRoute) {
        return <>{children}</>;
    }

    return (
        <>
            <SystemBootOverlay onStartupResolved={() => setIsStartupReady(true)} />
            {isStartupReady ? children : null}
        </>
    );
}
