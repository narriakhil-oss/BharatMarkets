"use client";

import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  variant?: "card" | "row" | "chart" | "ticker";
  count?: number;
  className?: string;
}

export function LoadingSkeleton({
  variant = "card",
  count = 1,
  className,
}: LoadingSkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i);

  if (variant === "ticker") {
    return (
      <div className={cn("grid grid-cols-2 md:grid-cols-4 gap-4", className)}>
        {items.map((i) => (
          <div
            key={i}
            className="flex flex-col gap-2 p-4 rounded-xl border border-white/[0.06] bg-card/40 backdrop-blur-md"
          >
            <div className="flex justify-between items-center">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-3 w-10" />
            </div>
            <Skeleton className="h-7 w-28" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "row") {
    return (
      <div className={cn("flex flex-col space-y-3", className)}>
        {items.map((i) => (
          <div
            key={i}
            className="flex items-center justify-between p-3 rounded-lg border border-white/[0.04] bg-white/[0.02]"
          >
            <div className="flex items-center space-x-3">
              <Skeleton className="h-9 w-9 rounded-md" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
            <div className="space-y-1 text-right">
              <Skeleton className="h-4 w-20 ml-auto" />
              <Skeleton className="h-3 w-12 ml-auto" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === "chart") {
    return (
      <Card className={cn("overflow-hidden border-white/[0.08] bg-card/60", className)}>
        <CardHeader className="space-y-2 pb-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-32" />
            <div className="flex gap-1.5">
              <Skeleton className="h-7 w-10 rounded-md" />
              <Skeleton className="h-7 w-10 rounded-md" />
              <Skeleton className="h-7 w-10 rounded-md" />
              <Skeleton className="h-7 w-10 rounded-md" />
            </div>
          </div>
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent>
          <div className="h-64 sm:h-80 w-full flex items-end gap-2 pt-6">
            {Array.from({ length: 24 }).map((_, idx) => {
              const heights = [
                "h-[35%]",
                "h-[50%]",
                "h-[40%]",
                "h-[65%]",
                "h-[80%]",
                "h-[55%]",
                "h-[70%]",
                "h-[45%]",
                "h-[60%]",
                "h-[75%]",
                "h-[90%]",
                "h-[50%]",
              ];
              const h = heights[idx % heights.length];
              return (
                <div
                  key={idx}
                  className="flex-1 flex flex-col justify-end items-center h-full"
                >
                  <Skeleton className={cn("w-full rounded-sm", h)} />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Default: Card
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-3", className)}>
      {items.map((i) => (
        <Card key={i} className="border-white/[0.08] bg-card/60">
          <CardHeader className="space-y-2">
            <div className="flex justify-between items-center">
              <Skeleton className="h-5 w-28" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
            <Skeleton className="h-3 w-40" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-8 w-32" />
            <div className="flex justify-between pt-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
