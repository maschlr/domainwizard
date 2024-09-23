"use client";

import { Button } from "@/components/ui/button";
import { MessageCircle } from "lucide-react";
import Link from "next/link";

export default function StickyButtons({ email = "feedback@urlwiz.io" }) {
	return (
		<div className="fixed bottom-12 right-4 z-50 flex flex-col space-y-4">
			<Button
				asChild
				size="icon"
				className="rounded-full w-12 h-12 shadow-lg"
				aria-label="Contact us via email"
			>
				<Link href={`mailto:${email}`}>
					<MessageCircle className="h-6 w-6" />
				</Link>
			</Button>
		</div>
	);
}
