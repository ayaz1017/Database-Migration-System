import React from 'react';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

export default function PageSkeleton() {
  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
      {/* Header Skeleton */}
      <div className="flex flex-col gap-3">
        <Skeleton height={36} width={250} baseColor="#1a1a24" highlightColor="#2a2a36" borderRadius={8} />
        <Skeleton height={20} width={400} baseColor="#1a1a24" highlightColor="#2a2a36" borderRadius={8} />
      </div>
      
      {/* Main Content Area Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Skeleton height={200} baseColor="#1a1a24" highlightColor="#2a2a36" borderRadius={12} />
          <Skeleton height={300} baseColor="#1a1a24" highlightColor="#2a2a36" borderRadius={12} />
        </div>
        <div className="space-y-6">
          <Skeleton height={150} baseColor="#1a1a24" highlightColor="#2a2a36" borderRadius={12} />
          <Skeleton height={350} baseColor="#1a1a24" highlightColor="#2a2a36" borderRadius={12} />
        </div>
      </div>
    </div>
  );
}
