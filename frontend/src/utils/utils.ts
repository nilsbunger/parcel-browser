export const asSqFt = (m) => Math.round(m * 3.28 * 3.28);
export const asFt = (m) => Math.round(m * 3.28);
export const ONEDAY = 1000 * 60 * 60 * 24; // in ms (time units)

export function snakeCaseToTitleCase(word: string) {
  const tokenized = word.toLowerCase().split('_');
  for (let i = 0; i < tokenized.length; i++) {
    tokenized[i] = tokenized[i][0].toUpperCase() + tokenized[i].slice(1);
  }
  return tokenized.join(' ');
}