"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import {
	Form,
	FormControl,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ReloadIcon } from "@radix-ui/react-icons";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Skeleton as SkeletonUI } from "@/components/ui/skeleton";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { fetcher } from "@/lib/utils";
import {
	AlarmClockCheck,
	CreditCard,
	ExternalLink,
	LockOpen,
	Pencil,
} from "lucide-react";
import type { DomainSearchResult, Listing, Skeleton } from "../lib/models";

function getTimeLeftStr(epoch: number) {
	const now = new Date();
	const secondsLeft = epoch - now.getTime() / 1000;
	const days = Math.floor(secondsLeft / (3600 * 24));
	const hours = Math.floor((secondsLeft % (3600 * 24)) / 3600);
	return `${days} days, ${hours} hours`;
}

const emailFormSchema = z.object({
	email: z.string().email({ message: "Invalid email address" }),
	name: z.string(),
});

export default function ResultList({ data }: { data: DomainSearchResult }) {
	const [isLoading, setIsLoading] = useState(false);
	const emailForm = useForm<z.infer<typeof emailFormSchema>>({
		resolver: zodResolver(emailFormSchema),
		defaultValues: {
			email: "",
		},
	});

	async function onSubmit(values: z.infer<typeof emailFormSchema>) {
		setIsLoading(true);
		const response = await fetcher.post(`/api/requests/${data.uuid}/unlock`, {
			...values,
		});
		setIsLoading(false);
		if (response.url) {
			window.location.href = response.url;
		} else {
			console.error("No redirect URL provided in the response");
		}
	}

	return (
		<div className="container w-11/12 lg:w-2-3 mx-auto pt-4">
			<Tabs asChild defaultValue="all">
				<TabsContent value="all">
					<Card>
						<CardHeader>
							<CardTitle className="text-2xl">Domain Listings</CardTitle>
							<CardDescription className="w-full flex flex-row flex-wrap justify-between pt-4 gap-4">
								<Button
									asChild
									size="lg"
									variant="outline"
									className="bg-primary text-white truncate border-primary max-w-full text-left h-auto py-3 px-4 space-x-3 transition-colors"
								>
									<Link href={`/requests/${data.uuid}/edit`}>
										<Pencil className="h-4 w-4 flex-shrink-0" />
										<span className="hidden md:block line-clamp-2 w-fit">
											{data.summary}
										</span>
									</Link>
								</Button>
								{!data.isUnlocked && (
									<Dialog>
										<DialogTrigger asChild>
											<Button
												size="lg"
												className="bg-primary text-white text-left h-auto py-3 px-4 max-w-full space-x-3 transition-colors"
											>
												<AlarmClockCheck className="h-4 w-4 flex-shrink-0" />
												<span className="hidden md:block line-clamp-2">
													Unlock
												</span>
											</Button>
										</DialogTrigger>
										<DialogContent className="sm:max-w-[425px] bg-white">
											<DialogHeader>
												<DialogTitle className="flex pb-4">
													<LockOpen className="h-4 w-4 flex-shrink-0" />
													<span className="pl-2">Top 5</span>
												</DialogTitle>
												<DialogDescription>
													What you will get:
													<ul className="list-disc pl-4">
														<li>
															Access to the{" "}
															<span className="font-semibold">
																top 5 domain listings
															</span>{" "}
															for your search query
														</li>
														<li>
															You request is{" "}
															<span className="font-semibold">
																updated daily
															</span>{" "}
															as new listings come in
														</li>
														<li>
															Your request is{" "}
															<span className="font-semibold">
																hidden from the{" "}
																<Link
																	className="text-primary decoration-solid"
																	href="/requests"
																>
																	public requests
																</Link>
															</span>
														</li>
														<li>
															You receive a{" "}
															<span className="font-semibold">
																daily emails
															</span>{" "}
															with the latest listings that fit your request
														</li>
													</ul>
												</DialogDescription>
											</DialogHeader>
											<Form {...emailForm}>
												<form
													onSubmit={emailForm.handleSubmit(onSubmit)}
													className="space-y-2"
												>
													<FormField
														control={emailForm.control}
														name="name"
														render={({ field }) => (
															<FormItem>
																<FormLabel>Name</FormLabel>
																<FormControl>
																	<Input placeholder="Joe Smith" {...field} />
																</FormControl>
																<FormMessage />
															</FormItem>
														)}
													/>
													<FormField
														control={emailForm.control}
														name="email"
														render={({ field }) => (
															<FormItem>
																<FormLabel>Email</FormLabel>
																<FormControl>
																	<Input
																		placeholder="joe.smith@example.com"
																		{...field}
																	/>
																</FormControl>
																<FormMessage />
															</FormItem>
														)}
													/>
													<DialogFooter className="pt-4">
														{isLoading ? (
															<Button className="flex flex-auto">
																<ReloadIcon className="h-4 w-4 mr-2 flex-shrink-0 animate-spin" />
																Loading ...
															</Button>
														) : (
															<Button type="submit">
																<CreditCard className="h-4 w-4 mr-2 flex-shrink-0" />
																Buy now
															</Button>
														)}
													</DialogFooter>
												</form>
											</Form>
										</DialogContent>
									</Dialog>
								)}
							</CardDescription>
						</CardHeader>
						<CardContent>
							<Table>
								<TableHeader>
									<TableRow>
										<TableHead className="hidden sm:table-cell">Rank</TableHead>
										<TableHead>URL</TableHead>
										<TableHead>Score</TableHead>
										<TableHead>Price</TableHead>
										<TableHead>Valuation</TableHead>
										<TableHead className="hidden md:table-cell">
											Auction Type
										</TableHead>
										<TableHead className="hidden md:table-cell">
											Auction End Time
										</TableHead>
									</TableRow>
								</TableHeader>
								<TableBody>
									{!data.isUnlocked &&
										data.skeletons &&
										data.skeletons.map((skeleton: Skeleton) => (
											<TableRow key={skeleton.rank}>
												<TableCell className="hidden sm:table-cell">
													{skeleton.rank}
												</TableCell>
												<TableCell className="font-medium">
													<SkeletonUI className="w-2/3 h-4 bg-slate-500" />
												</TableCell>
												<TableCell>{skeleton.score.toFixed(4)}</TableCell>
												<TableCell>${skeleton.price}</TableCell>
												<TableCell>${skeleton.valuation}</TableCell>
												<TableCell className="hidden md:table-cell">
													<SkeletonUI className="w-2/3 h-4 bg-slate-500" />
												</TableCell>
												<TableCell className="hidden md:table-cell">
													<SkeletonUI className="w-2/3 h-4 bg-slate-500" />
												</TableCell>
											</TableRow>
										))}
									{data.domains.map((listing: Listing) => (
										<TableRow key={listing.rank}>
											<TableCell className="hidden sm:table-cell">
												{listing.rank}
											</TableCell>
											<TableCell className="font-medium">
												<a
													href={listing.link}
													target="_blank"
													rel="noopener noreferrer"
													className="underline flex flex-row"
												>
													<ExternalLink className="mr-2 h-4 w-4" />
													{listing.url}
												</a>
											</TableCell>
											<TableCell>{listing.score.toFixed(4)}</TableCell>
											<TableCell>${listing.price}</TableCell>
											<TableCell>${listing.valuation}</TableCell>
											<TableCell className="hidden md:table-cell">
												<Link href={listing.link}>
													<Badge
														variant={
															listing.auctionType === "Bid"
																? "default"
																: "secondary"
														}
														className={
															listing.auctionType === "Bid"
																? "default"
																: "bg-purple-900"
														}
													>
														{" "}
														<span className="text-white">
															{listing.auctionType}
														</span>
													</Badge>
												</Link>
											</TableCell>
											<TableCell className="hidden md:table-cell">
												{new Date(
													listing.auctionEndTimeEpoch * 1000,
												).toLocaleString()}
												<span className="text-xs">
													{` (${getTimeLeftStr(listing.auctionEndTimeEpoch)})`}
												</span>
											</TableCell>
										</TableRow>
									))}
								</TableBody>
							</Table>
						</CardContent>
						<CardFooter>
							<div className="text-xs text-muted-foreground">
								Showing{" "}
								<strong>
									{data.skeletons.length + 1}-{data.totalDomains}
								</strong>{" "}
								of <strong>{data.totalDomains}</strong> domain listings
								{!data.isUnlocked && (
									<span className="text-xs">
										{" "}
										({data.skeletons.length} hidden)
									</span>
								)}
							</div>
						</CardFooter>
					</Card>
				</TabsContent>
			</Tabs>
		</div>
	);
}
