import { Message } from "@langchain/langgraph-sdk";

export function extractStringFromMessageContent(message: Message): string {
  return typeof message.content === "string"
    ? message.content
    : Array.isArray(message.content)
      ? message.content
          .filter((c: any) => c.type === "text" || typeof c === "string")
          .map((c: any) => (typeof c === "string" ? c : c.text || ""))
          .join("")
      : "";
}

/**
 * Safely serializes an object to JSON, handling circular references and non-serializable values
 * @param obj The object to serialize
 * @param space Optional formatting space
 * @returns JSON string or null if serialization fails
 */
export function safeStringify(obj: any, space?: string | number): string | null {
  const seen = new WeakSet();
  
  try {
    return JSON.stringify(obj, function(key, value) {
      // Skip Next.js async params and searchParams objects
      // These are Promises in Next.js 15+ and should not be serialized
      if (key === 'params' || key === 'searchParams') {
        // Check if it's a Promise or has Promise-like characteristics
        if (value && (typeof value.then === 'function' || value.constructor?.name === 'Promise')) {
          return undefined; // Skip async objects
        }
        // Also skip if it's an object that might trigger React.use() warnings
        if (value && typeof value === 'object' && !Array.isArray(value) && !isPlainObject(value)) {
          return undefined;
        }
      }
      
      // Handle circular references
      if (typeof value === "object" && value !== null) {
        if (seen.has(value)) {
          return "[Circular Reference]";
        }
        seen.add(value);
      }
      
      // Handle special types
      if (value instanceof Date) {
        return value.toISOString();
      }
      
      // Remove functions
      if (typeof value === "function") {
        return undefined;
      }
      
      // Remove DOM elements and React refs
      if (value instanceof HTMLElement) {
        return undefined;
      }
      
      // Remove undefined, symbols, and other non-serializable values
      if (value === undefined || typeof value === "symbol") {
        return undefined;
      }
      
      // Handle Error objects
      if (value instanceof Error) {
        return {
          name: value.name,
          message: value.message,
          stack: value.stack
        };
      }
      
      // Additional check for Next.js internal objects
      if (value && typeof value === 'object' && value.constructor) {
        const className = value.constructor.name;
        // Skip Next.js internal classes that might cause issues
        if (className.includes('NextRequest') || className.includes('NextResponse') || 
            className.includes('ReadonlyURLSearchParams') || className.includes('Promise')) {
          return undefined;
        }
      }
      
      return value;
    }, space);
  } catch (error) {
    console.error("Failed to stringify object:", error);
    return null;
  }
}

/**
 * Helper function to check if an object is a plain object
 * @param obj The object to check
 * @returns true if the object is a plain object
 */
function isPlainObject(obj: any): boolean {
  if (!obj || typeof obj !== 'object') return false;
  
  // Check if it's a plain object (not a built-in type)
  const proto = Object.getPrototypeOf(obj);
  if (!proto) return true;
  
  // Objects created by the Object constructor
  return proto === Object.prototype || proto === null;
}

/**
 * Deep clones an object while removing non-serializable properties
 * @param obj The object to clone
 * @param visited Optional WeakSet to track visited objects (prevents circular references)
 * @returns A clean, serializable copy of the object
 */
export function createSerializableClone<T>(obj: T, visited: WeakSet<any> = new WeakSet()): T {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
  // Handle primitives
  if (typeof obj !== "object") {
    return obj;
  }
  
  // Check for circular references
  if (visited.has(obj)) {
    return null as any; // Return null for circular references
  }
  visited.add(obj);
  
  // Handle Date objects
  if (obj instanceof Date) {
    return new Date(obj.toISOString()) as any;
  }
  
  // Handle arrays
  if (Array.isArray(obj)) {
    return obj.map(item => createSerializableClone(item, visited)) as any;
  }
  
  // Skip Next.js internal objects and Promises
  if (obj && typeof obj === 'object' && obj.constructor) {
    const className = obj.constructor.name;
    if (className === 'Promise' || className.includes('NextRequest') || 
        className.includes('NextResponse') || className.includes('ReadonlyURLSearchParams')) {
      return null as any;
    }
  }
  
  // Handle plain objects
  const cloned: any = {};
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      const value = obj[key];
      
      // Skip Next.js async params and searchParams
      if (key === 'params' || key === 'searchParams') {
        if (value && (typeof value === 'object' || typeof value?.then === 'function')) {
          continue; // Skip these async objects entirely
        }
      }
      
      // Skip non-serializable values
      if (
        typeof value === "function" ||
        typeof value === "symbol" ||
        value === undefined ||
        value instanceof HTMLElement ||
        (typeof value === "object" && value !== null && value.constructor && value.constructor.name === "RefImpl") ||
        (value && typeof value?.then === 'function') // Skip Promises
      ) {
        continue;
      }
      
      cloned[key] = createSerializableClone(value, visited);
    }
  }
  
  return cloned;
}

/**
 * Validates if an object can be safely serialized to JSON
 * @param obj The object to validate
 * @returns true if the object can be serialized, false otherwise
 */
export function isSerializable(obj: any): boolean {
  try {
    JSON.stringify(obj);
    return true;
  } catch {
    return false;
  }
}
