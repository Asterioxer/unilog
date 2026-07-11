import { useEffect } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}

export default function AnimatedCounter({
  value,
  duration = 0.8,
  decimals = 0,
  prefix = "",
  suffix = "",
  className = "",
}: AnimatedCounterProps) {
  const count = useMotionValue(0);
  
  const formatted = useTransform(count, (latest) => {
    return `${prefix}${latest.toFixed(decimals)}${suffix}`;
  });

  useEffect(() => {
    const controls = animate(count, value, { 
      duration,
      ease: "easeOut"
    });
    return () => controls.stop();
  }, [count, value, duration]);

  return (
    <motion.span data-testid="animated-counter" className={className}>
      {formatted}
    </motion.span>
  );
}
