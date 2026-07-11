type SkeletonProps = {
  className?: string;
};

export default function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div 
      data-testid="skeleton-element"
      className={`bg-muted animate-pulse rounded-md ${className}`} 
    />
  );
}
