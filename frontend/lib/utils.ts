import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

const headers = {
	"Content-Type": "application/json",
};

export const fetcher = {
	get: (url: string) =>
		fetch(url, { method: "GET", headers }).then((res) => res.json()),
	post: <T>(url: string, data: T) =>
		fetch(url, { method: "POST", headers, body: JSON.stringify(data) }).then(
			(res) => res.json(),
		),
	put: <T>(url: string, data: T) =>
		fetch(url, { method: "PUT", headers, body: JSON.stringify(data) }).then(
			(res) => res.json(),
		),
	delete: (url: string) =>
		fetch(url, { method: "DELETE", headers }).then((res) => res.json()),
};
