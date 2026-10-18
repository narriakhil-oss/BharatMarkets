import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-white/[0.06] backdrop-blur-xs",
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };
