export function TestButton({ children }) {
  return (
    <button className="btn-primary btn-sm p-2 rounded bg-blue-500 hover:bg-blue-600 transition">
      {children}
    </button>
  );
}