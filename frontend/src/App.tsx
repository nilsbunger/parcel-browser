import {TestButton} from "./TestButton";


export function App() {
    return (
        <div className="min-h-full">
            <div className="h-1 w-full bg-pinkpop"></div>
            <div className="md:container px-8 lg:px-16 py-10">
                <h1>Hello world!</h1>
                <TestButton>Hello</TestButton>
            </div>
        </div>
    )
}