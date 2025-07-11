"use client";

export default function LoadingIndicator({ isLoading }) {
  if (!isLoading) return null;

  return (
    <div className="mt-4 flex justify-center">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      <span className="ml-2 text-sm text-gray-600">
        Processing...
      </span>
    </div>
  );
}
