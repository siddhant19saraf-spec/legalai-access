'use client';

export function LoadingSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`${className} animate-pulse space-y-4`} aria-hidden="true">
      <div className="h-6 bg-gray-200 rounded w-3/4 max-w-md" />
      <div className="h-4 bg-gray-200 rounded w-full" />
      <div className="h-4 bg-gray-200 rounded w-5/6" />
      <div className="h-4 bg-gray-200 rounded w-4/6" />
      <div className="h-32 bg-gray-200 rounded-lg" />
      <div className="h-32 bg-gray-200 rounded-lg" />
      <div className="h-32 bg-gray-200 rounded-lg" />
    </div>
  );
}

export function ResponseSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-hidden="true">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="h-8 bg-gray-200 rounded w-1/4" />
        <div className="flex flex-wrap gap-2">
          <div className="h-6 bg-gray-200 rounded-full w-24" />
          <div className="h-6 bg-gray-200 rounded-full w-28" />
          <div className="h-6 bg-gray-200 rounded-full w-24" />
          <div className="h-6 bg-gray-200 rounded-full w-20" />
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="h-6 bg-gray-200 rounded w-1/5" />
        <div className="h-5 bg-gray-200 rounded w-full" />
        <div className="h-4 bg-gray-200 rounded w-full" />
        <div className="h-4 bg-gray-200 rounded w-5/6" />
        <div className="h-4 bg-gray-200 rounded w-4/6" />
      </div>
      
      <div className="space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/5" />
        <div className="p-4 bg-gray-100 rounded-lg border space-y-3">
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-4/5" />
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="h-6 bg-gray-200 rounded w-1/5" />
        <div className="space-y-2">
          <div className="h-16 bg-gray-100 rounded-lg border" />
          <div className="h-16 bg-gray-100 rounded-lg border" />
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="h-6 bg-gray-200 rounded w-1/5" />
        <div className="space-y-2">
          <div className="h-8 bg-gray-100 rounded-lg" />
          <div className="h-8 bg-gray-100 rounded-lg w-5/6" />
        </div>
      </div>
      
      <div className="pt-4 border-t">
        <div className="h-4 bg-gray-200 rounded w-1/2" />
      </div>
      
      <div className="space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/5" />
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-200 rounded-lg border" />
          <div className="w-10 h-10 bg-gray-200 rounded-lg border" />
          <div className="w-10 h-10 bg-gray-200 rounded-lg border" />
          <div className="w-10 h-10 bg-gray-200 rounded-lg border" />
          <div className="w-10 h-10 bg-gray-200 rounded-lg border" />
        </div>
      </div>
    </div>
  );
}

export function QuestionInputSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-hidden="true">
      <div className="space-y-2">
        <div className="h-5 bg-gray-200 rounded w-1/4" />
        <div className="h-12 bg-gray-200 rounded-lg" />
        <div className="h-12 bg-gray-200 rounded-lg" />
        <div className="h-12 bg-gray-200 rounded-lg" />
        <div className="h-12 bg-gray-200 rounded-lg" />
        <div className="h-12 bg-gray-200 rounded-lg" />
      </div>
      
      <div className="space-y-2">
        <div className="h-5 bg-gray-200 rounded w-1/4" />
        <div className="h-10 bg-gray-200 rounded-lg" />
      </div>
      
      <div className="space-y-2">
        <div className="h-5 bg-gray-200 rounded w-1/4" />
        <div className="h-10 bg-gray-200 rounded-lg" />
      </div>
      
      <div className="flex items-center gap-4 pt-2">
        <div className="h-10 bg-gray-200 rounded-lg w-40" />
        <div className="h-10 bg-gray-200 rounded-lg w-40" />
      </div>
    </div>
  );
}

export function SourceCardSkeleton() {
  return (
    <article className="p-4 bg-white border border-gray-200 rounded-xl animate-pulse" aria-hidden="true">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="h-5 bg-gray-200 rounded w-24" />
        <div className="h-5 bg-gray-200 rounded w-20" />
        <div className="h-5 bg-gray-200 rounded w-20" />
      </div>
      <div className="mt-2 h-4 bg-gray-200 rounded w-3/4" />
      <div className="mt-1 h-3 bg-gray-200 rounded w-1/2 font-mono" />
      <div className="mt-2 h-6 bg-gray-200 rounded w-5/6" />
      <div className="mt-2 h-8 bg-gray-200 rounded w-1/3" />
    </article>
  );
}