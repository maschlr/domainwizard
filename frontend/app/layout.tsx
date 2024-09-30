import StickyButtons from "@/components/stickyButtons";
import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import GoogleAnalytics from "@/components/GoogleAnalytics";
import Link from "next/link";
import { Suspense } from "react";

const geistSans = localFont({
	src: "./fonts/GeistVF.woff",
	variable: "--font-geist-sans",
	weight: "100 900",
});
const geistMono = localFont({
	src: "./fonts/GeistMonoVF.woff",
	variable: "--font-geist-mono",
	weight: "100 900",
});
const fondamento = localFont({
	src: "./fonts/Fondamento-Regular.ttf",
	variable: "--font-fondamento",
});

export const metadata: Metadata = {
	title: "URL Wizard",
	description: "Find the perfect URL for your next project",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en">
			<body
				className={`${geistSans.variable} ${geistMono.variable} antialiased`}
			>
				<header className="flex justify-center pt-8">
					<p
						style={fondamento.style}
						className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-900 text-4xl font-bold "
					>
						<Link href="/" className="drop-shadow-md">
							urlwiz.io
						</Link>
					</p>
				</header>
				{children}
				<StickyButtons />
				<Suspense fallback={null}>
					<GoogleAnalytics />
				</Suspense>
			</body>
		</html>
	);
}
