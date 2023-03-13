

export default function BackyardPage() {
  return (
    <div>        
      <div className='md:container md:mx-auto md:w-8/12'>        
        <img src="/images/louisiana_rendering.png" className="w-full" />
        <div className="hero bg-base-200 mb-8">
        <div className="hero-content text-center">
          <div className="max-w-lg">
            <h1 className="text-5xl font-bold">The Backyard SPV</h1>
            <p className="py-6">Local development team <b>Backyard</b> is building 19 "missing middle" residential units across three lots in San Diego's hip North Park and Normal Heights neighborhoods. The project is underwritten to a 6.3% UYOC and investor IRR of 16% to 18%, with an exit timeline of 6 to 10 years. Home3 secured a $1M equity allocation offered to our network of investors.</p>
            <button className="btn btn-primary">Apply to invest</button>
          </div>
        </div>
        </div>
        
        <article className='prose'>        
          <h1>Locations</h1>
          <p>The sites are short walks to vibrant commercial corridors and frequent transit, sub-15 minutes drive to downtown San Diego, and sub-30 minutes drive to Apple’s planned 5,000 employee Rancho Bernardo engineering campus.</p>
          <p>The project benefits from <a href='https://www.zumper.com/rent-research/san-diego-ca/north-park'>17% annual rent growth</a> in its submarket, drawing on San Diego’s <a  href='https://www.sandiegouniontribune.com/news/politics/story/2023-02-10/san-diego-tax-revenue-fully-recovered-from-pandemic-plunge'>nation-leading pandemic recovery</a></p>
          <p>The New York Times <a target='_blank' href='https://www.nytimes.com/interactive/2023/03/09/realestate/san-diego-houses-homes.html'>just recognized</a> North Park as "one of San Diego’s trendiest neighborhoods". They called Normal Heights, which is just east, "a colorful, walkable neighborhood with craft-beer pubs, pizzerias and vegetarian restaurants". Both neighborhoods are emerging as prime destinations for urban-minded professionals. Their ecletic, upscale vibe and proximity to a major park reminds us of Dolores Heights in San Francisco.</p>
          <img src="/images/SD_property_map.jpeg"/>                
          <h2>Development Plan</h2>
          <p>[design philosophy, what they're building]</p>
          <table className="table-zebra table-fixed">          
            <thead>
              <tr>                
                <th className="w-32"><b>Address</b></th>
                <th><b>Plan</b></th>              
                <th><b>Status</b></th>
              </tr>
            </thead>
            <tbody>          
              <tr>                
                <td>4777 35th st</td>
                <td>Build 2x 2BR townhomes in the back, renovate existing single family home</td>
                <td>Construction nearly complete</td>              
              </tr>            
              <tr>                
                <td>3322 Nile St</td>
                <td>Build 1x 1BR and 1x 2BR in the back, renovate existing 2x 1BR in front duplex</td>              
                <td>In permitting</td>              
              </tr>            
              <tr>
                <td>4137 Louisiana St</td>
                <td>Tear down existing single family home and build 12 new units: 9x 1BR, 2x 2BR, 1x 3BR</td>   
                <td>Pre-permitting</td>                         
              </tr>
            </tbody>
          </table>  
          <h2>Renderings</h2>           
          <div className="carousel w-full">
          <div id="slide1" className="carousel-item relative w-full">
            <img src="/images/35th.jpeg" className="w-full" />
            <div className="absolute flex justify-between transform -translate-y-1/2 left-5 right-5 top-1/2">
              <a href="#slide4" className="btn btn-circle">❮</a> 
              <a href="#slide2" className="btn btn-circle">❯</a>
            </div>
          </div> 
          <div id="slide2" className="carousel-item relative w-full">
            <img src="/images/nile.jpeg" className="w-full" />
            <div className="absolute flex justify-between transform -translate-y-1/2 left-5 right-5 top-1/2">
              <a href="#slide1" className="btn btn-circle">❮</a> 
              <a href="#slide3" className="btn btn-circle">❯</a>
            </div>
          </div> 
          <div id="slide3" className="carousel-item relative w-full">
            <img src="/images/louisiana.jpeg" className="w-full" />
            <div className="absolute flex justify-between transform -translate-y-1/2 left-5 right-5 top-1/2">
              <a href="#slide2" className="btn btn-circle">❮</a> 
              <a href="#slide4" className="btn btn-circle">❯</a>
            </div>
          </div>           
        </div>        
        </article>
        <article className="prose">
          <h2>Summary of Financials</h2>          
          <p><a className="link link-hover" href="https://docs.google.com/spreadsheets/d/1GKYBgWJvSQli0nq67URbhf_Mkovb5NefA_v3M5LJJw4/edit?usp=sharing" target="_blank">📊 Financial model (Google Sheet)</a></p>                      
          <p>
            Originally underwritten for an investor IRR of 16%-18% and unlevered yield on cost (UYOC) of 6.3%. 
          </p>
          <p>Increased financing rates are cooling the Southern California construction market, which brings the potential for decreased labor costs and supports future rent growth.</p>
          <p>Waterfall and fees</p>
          <ul>
            <li>Promote structure</li> 
            <li>X acquisition fee</li>
            <li>No AUM fee</li>
          </ul>          
          <h3>The Home3 SPV</h3>
          <p>Home3 secured a $1M allocation as primary LP. Our promote and fees stack on top of Backyard's. To mitigate the impact of double fees, we secured an XX discount on Backyard's promote structure via a side letter.</p>
          <ul><li>X% AUM fee</li><li>Promote structure</li></ul>
          <h2>Backyard Team</h2>
          <p>[about the team]</p>
          <figure><img src="/images/RoeeAndGabe.jpg" alt="Roee and Gabe from Backyard" /></figure>
          <h2>Deal Documents</h2>                          
          <p>
            <ul><li><a className="link link-hover" href="#">📄 Investment Memo</a></li>
            <li><a className="link link-hover" href="#">📄 2022 Q3 Update</a></li>
            <li><a className="link link-hover" href="#">📄 Home3 Side Letter</a></li>
            </ul>
          </p>
          <h2>Next Steps</h2>
          <p>Reach out to marcio@home3.co with any questions about this deal.</p>
          <button className="btn btn-primary mb-12">Apply to invest</button>          
        </article>        
      </div>
    </div>    
  )
}

