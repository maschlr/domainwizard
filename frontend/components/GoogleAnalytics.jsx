"use client";

import { usePathname, useSearchParams } from "next/navigation";
import Script from "next/script";
import { Suspense, useEffect } from "react";
import ReactGA from "react-ga4";

const GA_MEASUREMENT_ID = "G-B2NXZBR1TJ";

export default function GoogleAnalytics() {
	const pathname = usePathname();
	const searchParams = useSearchParams();

	useEffect(() => {
		ReactGA.initialize(GA_MEASUREMENT_ID);
	}, []);

	useEffect(() => {
		const url = pathname + searchParams.toString();
		ReactGA.send({ hitType: "pageview", page: url });
	}, [pathname, searchParams]);

	return (
		<Suspense>
			<Script
				strategy="afterInteractive"
				src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
			/>
			<Script id="gtag-init" strategy="afterInteractive">
				{`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', '${GA_MEASUREMENT_ID}', {
            page_path: window.location.pathname,
          });
        `}
			</Script>
		</Suspense>
	);
}
