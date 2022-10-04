export const asSqFt = (m) => Math.round(m * 3.28 * 3.28);
export const asFt = (m) => Math.round(m * 3.28);
export const ONEDAY = 1000 * 60 * 60 * 24; // in ms (time units)

export function snakeCaseToTitleCase(word: string): string {
  const tokenized = word.toLowerCase().split('_');
  for (let i = 0; i < tokenized.length; i++) {
    tokenized[i] = tokenized[i][0].toUpperCase() + tokenized[i].slice(1);
  }
  return tokenized.join(' ');
}

// Stringify alternative that supports circular references and depth limiter
// Credit: https://stackoverflow.com/questions/13861254/json-stringify-deep-objects/57193345#57193345
/** A more powerful version of the built-in JSON.stringify() function that uses the same function to respect the
 * built-in rules while also limiting depth and supporting cyclical references.
 */
export function stringify(val: any, depth?: number, replacer?: (this: any, key: string, value: any) => any, space?: string | number, onGetObjID?: (val: object) => string): string {
  depth = isNaN(+depth) ? 1 : depth;
  const recursMap = new WeakMap();

  function _build(val: any, depth: number, o?: any, a?: boolean, r?: boolean) {
    return !val || typeof val != 'object' ? val
      : (r = recursMap.has(val),
        recursMap.set(val, true),
        a = Array.isArray(val),
        r ? (o = onGetObjID && onGetObjID(val) || null) : JSON.stringify(val, function (k, v) {
          if (a || depth > 0) {
            if (replacer) v = replacer(k, v);
            if (!k) return (a = Array.isArray(v), val = v);
            !o && (o = a ? [] : {});
            o[k] = _build(v, a ? depth : depth - 1);
          }
        }),
        o === void 0 ? (a ? [] : {}) : o);
  }

  return JSON.stringify(_build(val, depth), null, space);
}