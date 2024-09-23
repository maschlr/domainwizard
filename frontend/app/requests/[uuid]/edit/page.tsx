"use client";

import TextareaForm from "@/components/textareaForm";
import type { DomainSearchResult } from "@/lib/models";
import { fetcher } from "@/lib/utils";
import { useMemo, useState } from "react";
import useSWR from "swr";

import LoadingPage from "@/components/loadingPage";

export default function DomainSearchEdit({
	params,
}: {
	params: { uuid: string };
}) {
	const { data, error, isLoading } = useSWR(
		`/api/requests/${params.uuid}`,
		fetcher.get,
	);
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
	useMemo(() => {
		setDomainSearchResult(data);
	}, [data]);

	if (isLoading) return <LoadingPage />;
	if (error) return <div>Error: {error}</div>;

	return (
		<div className="h-auto pt-20 pb-0 gap-16 font-[family-name:var(--font-geist-sans)]">
			<main className="flex justify-center w-full">
				<TextareaForm domainSearchResult={domainSearchResult} />
			</main>
		</div>
	);
}
