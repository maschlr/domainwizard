export interface Listing {
	rank: number;
	url: string;
	pageviews: number;
	valuation: number;
	monthlyParkingRevenue: number;
	isAdult: boolean;
	link: string;
	auctionType: string;
	auctionEndTime: string;
	auctionEndTimeEpoch: number;
	price: number;
	numberOfBids: number;
	domainAge: number;
	score: number;
}

export interface Skeleton {
	rank: number;
	price: number;
	pageviews: number;
	valuation: number;
	score: number;
}

export interface DomainSearchResult {
	domains: Listing[];
	skeletons: Skeleton[];
	uuid: string;
	totalDomains: number;
	isUnlocked: boolean;
	prompt: string;
	summary: string;
	isExample: boolean;
}
