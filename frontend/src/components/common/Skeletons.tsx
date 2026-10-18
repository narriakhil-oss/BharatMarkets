"use client";

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-zinc-800/60 ${className}`} />;
}

export function IndexCardSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-4 backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-4 w-12" />
      </div>
      <Skeleton className="h-8 w-36 mb-3" />
      <div className="flex items-center gap-2 mb-4">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-14" />
      </div>
      <div className="space-y-1.5 pt-2 border-t border-zinc-800/50">
        <div className="flex justify-between">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="h-1.5 w-full rounded-full" />
      </div>
    </div>
  );
}

export function MoversTableSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <div className="h-6 w-32 bg-zinc-800/70 rounded animate-pulse" />
        <div className="h-5 w-16 bg-zinc-800/50 rounded-full animate-pulse" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between py-2 border-b border-zinc-800/40">
            <div className="flex items-center gap-3">
              <Skeleton className="h-4 w-4" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-3 w-32 hidden md:block" />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-5 w-14 rounded-md" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function HeatmapSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <div className="space-y-1">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-60" />
        </div>
        <div className="flex gap-1.5">
          <Skeleton className="h-8 w-12 rounded-lg" />
          <Skeleton className="h-8 w-12 rounded-lg" />
          <Skeleton className="h-8 w-12 rounded-lg" />
        </div>
      </div>
      <Skeleton className="h-72 w-full rounded-lg" />
    </div>
  );
}

export function BreadthSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-4 w-20" />
      </div>
      <Skeleton className="h-4 w-full rounded-full mb-3" />
      <div className="flex justify-between">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-3 w-28" />
      </div>
    </div>
  );
}
