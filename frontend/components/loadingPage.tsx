import { ReloadIcon } from "@radix-ui/react-icons";

export default function LoadingPage() {
	return (
		<div className="mt-12 w-full h-full flex items-center">
			<ReloadIcon className="h-8 w-8 animate-spin mx-auto" />
		</div>
	);
}
