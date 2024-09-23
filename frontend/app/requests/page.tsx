"use client";

import LoadingPage from "@/components/loadingPage";
import { Card, CardContent } from "@/components/ui/card";
import { fetcher } from "@/lib/utils";
import { Link, Star } from "lucide-react";
import useSWR from "swr";

import type { DomainSearchResult } from "../../lib/models";

export default function Requests() {
	const { data, error, isLoading } = useSWR("/api/requests", fetcher.get);

	if (isLoading) return <LoadingPage />;
	if (error) return <div>Error: {error}</div>;

	return (
		<div className="mx-auto w-fit pt-8">
			<h2 className="text-2xl font-bold mb-4">Domain Searches</h2>
			<ul className="space-y-4">
				{data.map((searchResult: DomainSearchResult) => (
					<li key={data.uuid}>
						<Card className="overflow-hidden m-4">
							<CardContent className="p-4 flex items-start space-x-4">
								<Star
									className={`${"flex-shrink-0"}  ${
										searchResult.isExample ? "fill-black" : "fill-transparent"
									}`}
								/>
								<a
									className="underline flex flex-grow"
									href={`/requests/${searchResult.uuid}`}
								>
									<Link className="mr-2 h-4 w-4" />
									{searchResult.summary}
								</a>
							</CardContent>
						</Card>
					</li>
				))}
			</ul>
		</div>
	);
}
