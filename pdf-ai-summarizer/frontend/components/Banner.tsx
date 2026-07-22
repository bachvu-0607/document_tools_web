import { AlertIcon, CheckIcon } from "@/components/ui/icons";

type BannerVariant = "error" | "success";

type BannerProps = {
  variant: BannerVariant;
  children: string;
};

const variantStyles: Record<BannerVariant, string> = {
  error:
    "border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/60 dark:text-red-200",
  success:
    "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/60 dark:text-emerald-200",
};

export function Banner({ variant, children }: BannerProps) {
  const Icon = variant === "error" ? AlertIcon : CheckIcon;

  return (
    <div className={`flex items-center gap-2 rounded-xl border px-4 py-3 text-sm ${variantStyles[variant]}`}>
      <Icon className="h-4 w-4 shrink-0" />
      <span>{children}</span>
    </div>
  );
}
