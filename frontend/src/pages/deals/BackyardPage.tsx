

export default function BackyardPage() {
  return (
    <div>
      <h1>Backyard Page!!</h1>
      <div className="card w-96 bg-base-100 shadow-xl">
        <figure><img src="/images/RoeeAndGabe.jpg" alt="Roee and Gabe from Backyard" /></figure>
        <div className="card-body">
          <h2 className="card-title">Shoes!</h2>
          <p>If a dog chews shoes whose shoes does he choose?</p>
          <div className="card-actions justify-end">
            <button className="btn btn-primary">Buy Now</button>
          </div>
        </div>
      </div>
    </div>

  )
}

