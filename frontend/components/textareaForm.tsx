"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ReloadIcon } from "@radix-ui/react-icons";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
	Form,
	FormControl,
	FormField,
	FormItem,
	FormLabel,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { fetcher } from "@/lib/utils";
import type { DomainSearchResult } from "../lib/models";
import LoadingPage from "./loadingPage";

const FormSchema = z.object({
	websiteDescriptionPrompt: z.string(),
});

enum TextareaFormState {
	NEW = 0,
	LOADING = 1,
	SUCCESS = 2,
}

export default function TextareaForm({
	domainSearchResult,
}: { domainSearchResult: DomainSearchResult }) {
	const [state, setState] = useState<TextareaFormState>(TextareaFormState.NEW);
	const [description, setDescription] = useState("");
	const { data, error, isLoading } = useSWR("/api/count", fetcher.get);

	const router = useRouter();
	const form = useForm<z.infer<typeof FormSchema>>({
		resolver: zodResolver(FormSchema),
	});
	const textareaRef = useRef<HTMLTextAreaElement>(null);
	useEffect(() => {
		if (textareaRef.current && description) {
			textareaRef.current.style.height = "auto";
			textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
		}
	}, [description]);

	useMemo(() => {
		setDescription(domainSearchResult.prompt);
	}, [domainSearchResult.prompt]);

	if (error) return <div>failed to load</div>;
	if (isLoading) return <LoadingPage />;

	async function onSubmit() {
		setState(TextareaFormState.LOADING);
		const payload = {
			prompt: description,
		};
		const result: DomainSearchResult = await fetcher.post(
			"/api/requests",
			payload,
		);
		if (result.uuid) {
			router.push(`/requests/${result.uuid}`);
		} else setState(TextareaFormState.NEW);
	}
	const textAreaClassName =
		"w-full min-h-[100px] p-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all duration-200 ease-in-out";

	return (
		<div className="container grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8 w-fit mb-10">
			<Form {...form}>
				<form className="w-full max-w-2xl mx-auto pt-4 space-y-4">
					<FormField
						control={form.control}
						name="websiteDescriptionPrompt"
						render={({ field }) => (
							<FormItem>
								<FormLabel className="text-lg">
									Search
									<span className="font-bold text-primary"> {data} </span>
									domain listings
								</FormLabel>
								<FormControl>
									<Textarea
										placeholder="What do you want to build today? Please give a brief description of your project."
										className={textAreaClassName}
										disabled={state !== TextareaFormState.NEW}
										{...field}
										value={description}
										ref={textareaRef}
										onChange={(e) => setDescription(e.target.value)}
									/>
								</FormControl>
							</FormItem>
						)}
					/>
					<div className="container grid justify-items-end">
						{state === TextareaFormState.NEW && (
							<Button
								type="submit"
								className="transition ease-in-out delay-150 hover:-translate-y-1 hover:scale-105 hover:drop-shadow duration-300 text-white bg-primary"
								onClick={() => onSubmit()}
							>
								Submit
							</Button>
						)}
						{state === TextareaFormState.LOADING && (
							<Button disabled>
								<ReloadIcon className="mr-2 h-4 w-4 animate-spin" />
								Loading...
							</Button>
						)}
						{state === TextareaFormState.SUCCESS && (
							<Button
								onClick={() => setState(TextareaFormState.NEW)}
								className="text-white"
								type="submit"
							>
								Edit
							</Button>
						)}
					</div>
				</form>
			</Form>
		</div>
	);
}
