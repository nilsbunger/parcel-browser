import useSWR from "swr";

const fetcher = (...args) => fetch(...args).then(res => res.json())


export function ListingsPage() {
    const {data, error} = useSWR('/api/user', fetcher)

    if (error) return <div>failed to load</div>
    if (!data) return <div>loading...</div>

    return (<>
            <h1>Hello world from pages/ListingsPage.tsx!</h1>
        </>
    )
}