// Input — shadcn-style tối giản
import { cn } from '@/lib/utils';
import { forwardRef, type InputHTMLAttributes } from 'react';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm',
        'placeholder:text-gray-400',
        'focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100',
        'disabled:cursor-not-allowed disabled:bg-gray-100',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';
