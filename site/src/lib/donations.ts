/**
 * Donation addresses — the single source of truth for every locale.
 *
 * Deliberately NOT part of the per-locale dictionaries: a wallet address is
 * not translatable copy, and duplicating it across five files is exactly how
 * one of them ends up with a typo. Dicts carry only the surrounding prose.
 *
 * `asset` and `network` are brand tokens and stay untranslated everywhere.
 */
export interface DonationAddress {
  asset: string;
  network: string;
  address: string;
}

export const DONATIONS: DonationAddress[] = [
  { asset: 'GRAM', network: 'TON', address: 'UQC_UNDyKIbeAy7qhTG8b6lFIJL3eyYwZit6pxQRtZZ6Dzo6' },
  { asset: 'USDT', network: 'TON', address: 'UQC_UNDyKIbeAy7qhTG8b6lFIJL3eyYwZit6pxQRtZZ6Dzo6' },
  { asset: 'USDT', network: 'Tron (TRC-20)', address: 'TZ3K36oh6FbpMvxncBwxqPzTC6NnHYQ1pL' },
  { asset: 'ETH', network: 'Ethereum (ERC-20)', address: '0x5F3FbC45A723c92a4797D98ECeE991f2a7b6eec6' },
  { asset: 'SOL', network: 'Solana', address: 'ACpEC9m3MuacKL4wwEnfTKGCNNDHuvaKdPLD7DuFvvvB' },
  { asset: 'BTC', network: 'Bitcoin', address: 'bc1q9zx6y445lqryl60z3phfekqajyjs45meex4cd4' },
];
