import { twMerge } from "tailwind-merge";
import clsx, { type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export async function waitForJobStatus(
  jobId: string,
  target = "uploaded",
  interval = 1000,
): Promise<{ status: string }> {
  while (true) {
    const res = await fetch(`/status/${jobId}`);
    const data = await res.json();
    if (data.status === target) {
      return data;
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }
}

