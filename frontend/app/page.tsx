"use client";

import TextareaForm from "@/components/textareaForm";
import Link from "next/link";
import { useState } from "react";

import type { DomainSearchResult } from "../lib/models";
export default function Home() {
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	const [domainSearchResult, setDomainSearchResult] =
		useState<DomainSearchResult>({
			domains: [],
			skeletons: [],
			uuid: "",
			totalDomains: 0,
			isUnlocked: false,
			prompt: "",
			summary: "",
			isExample: false,
		});
	return (
		<div className="h-auto pt-20 pb-0 gap-16 font-[family-name:var(--font-geist-sans)]">
			<main className="flex justify-center w-full">
				<TextareaForm domainSearchResult={domainSearchResult} />
				<div className="fixed bottom-4 z-50 flex flex-col w-auto">
					<p className="text-sm text-gray-500">
						Check out
						<Link className="text-primary" href="/requests">
							{" "}
							other search requests
						</Link>
					</p>
				</div>
			</main>
		</div>
	);
}
