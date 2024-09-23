"use client";

import useSWR from "swr";

import LoadingPage from "@/components/loadingPage";
import ResultList from "@/components/resultList";
import { fetcher } from "@/lib/utils";

export default function Request({ params }: { params: { uuid: string } }) {
	const { data, error, isLoading } = useSWR(
		`/api/requests/${params.uuid}`,
		fetcher.get,
	);
	if (isLoading) return <LoadingPage />;
	if (error) return <div>Error: {error}</div>;
	console.log(data);
	const result = data;

	return (
		<div>
			<ResultList data={result} />
		</div>
	);
}
