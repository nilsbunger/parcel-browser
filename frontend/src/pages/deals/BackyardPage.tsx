export default function BackyardPage() {
  return (
    <div>        
      <div className='md:container md:mx-auto md:w-8/12'>        
        <img src="/images/louisiana_rendering.png" className="w-full" />
        <div className="hero bg-base-200 mb-8">
        <div className="hero-content text-center">
          <div className="max-w-xl2">
            <h1 className="text-5xl font-bold">The Backyard-Home3 SPV</h1>
            <p className="py-6">Local development team <b>Backyard</b> is building 19 "missing middle" residential units across three lots in San Diego's hip North Park and Normal Heights neighborhoods. The project is underwritten to a 6.3% UYOC and investor IRR of 16% to 18%, with an exit timeline of 6 to 10 years. <b>Home3</b> secured a $1M equity allocation, exclusively offered to our network of investors.</p>
            <form action="https://forms.gle/o4uhhDWYWZAzzMSc6" method="get" target="_blank">
              <button className="btn btn-primary">Apply to invest</button>
            </form>            
          </div>
        </div>
        </div>
        
        <article className='prose max-w-full'>  
          <h1>Why we like this deal</h1>          
          <ul>
              <li><strong>Location, x3</strong>. The sites are well positioned in and around North Park, one of the strongest submarkets in San Diego. The city has a diverse economy and has arguably the strongest post-pandemic recovery in the country.</li>
              <li><strong>Promising team.&nbsp;</strong>Roee, Coby and Gabe amassed considerable real estate experience working with their families and professional firms, have a deep understanding of their market and target tenants, and are in a city that&apos;s hungry for their style of development. They are strongly committed to rewarding their investors as a necessary ingredient to continue their career growth.</li>
              <li><strong>Margin of safety.&nbsp;</strong>The project is utilizing reasonable leverage (64% LTV), the GPs have skin in the game (family equity is ~10% of total project cost), and secured construction financing for 2 of 3 projects at low rates (8%). All three project sites were acquired before a recent 28% increase in prices, and they are being developed sequentially, creating the option to hold or sell the last site if appropriate. These items provides an exit path in case of a bear-case scenario.</li>
          </ul>
          <p>We encourage all investors to perform their own dilligence. As always, Real Estate investments are inherently risky and can go to zero due to a variety of factors within and outside the GP's control.</p>
          <h1>Locations</h1>
          <p>The sites are short walks to vibrant commercial corridors and frequent transit, sub-15 minutes drive to downtown San Diego, and sub-30 minutes drive to <a target="blank" href="https://appleinsider.com/articles/22/07/27/apple-buys-new-campus-for-445-million-for-vast-san-diego-expansion">Apple’s planned 5,000 employee Rancho Bernardo engineering campus</a>. Backyard chose the sites because they’re in walkable neighborhoods close to desirable amenities like restaurants, cafes, parks, boutique shops, and cultural institutions. These locations command a higher premium because demand to live in walkable, mixed-use neighborhoods considerably outpaces supply.</p>
          <img src="/images/SD_property_map.jpeg"/>
          <p>The project benefits from <a href='https://www.zumper.com/rent-research/san-diego-ca/north-park'>17% annual rent growth</a> in its submarket, drawing on San Diego’s <a  href='https://www.sandiegouniontribune.com/news/politics/story/2023-02-10/san-diego-tax-revenue-fully-recovered-from-pandemic-plunge'>nation-leading pandemic recovery</a></p>
          <p>The New York Times <a target='_blank' href='https://www.nytimes.com/interactive/2023/03/09/realestate/san-diego-houses-homes.html'>just recognized</a> North Park as "one of San Diego’s trendiest neighborhoods". They called Normal Heights, which is adjacent to the east, "a colorful, walkable neighborhood with craft-beer pubs, pizzerias and vegetarian restaurants". Both neighborhoods are emerging as prime destinations for urban-minded professionals. Their ecletic, upscale vibe and proximity to a major park reminds us of Dolores Heights in San Francisco.</p>
          <h2>Development Plan</h2>          
          <p>
          The three sites are in process of being developed into 3-12 units each, through value add improvements and/or ground up development. The design philosophy caters to high-end renters, with thoughtful touches like balconies, floor-to-ceiling windows, and quality finishes. 
          </p>
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
                <td>Construction nearly complete, occupancy expected in Q3.</td>              
              </tr>            
              <tr>                
                <td>3322 Nile St</td>
                <td>Build 1x 1BR and 1x 2BR in the back, renovate existing 2x 1BR in front duplex</td>              
                <td>In permitting, construction expected in Q2.</td>              
              </tr>            
              <tr>
                <td>4137 Louisiana St</td>
                <td>Tear down existing single family home and build 12 new units: 9x 1BR, 2x 2BR, 1x 3BR</td>   
                <td>Pre-permitting. Construction expected in 2024, pending financing.</td>                         
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
        <article className="prose max-w-full mb-12">
          <h2>Financials</h2>                          
          <h3>The Backyard entity ("InvestCo")</h3>
          <p><a className="link link-hover" href="https://docs.google.com/spreadsheets/d/1GKYBgWJvSQli0nq67URbhf_Mkovb5NefA_v3M5LJJw4/edit?usp=sharing" target="_blank">📊 Pro Forma (Google Sheet)</a></p>
          <b>Site Summary</b>
          <p><i>scroll table to see all columns</i></p>
          <div className="overflow-x-scroll">
          <table className="table table-zebra table-auto">
          <thead>
            <tr><td>Address</td><td>Units</td><td>All-in-cost</td><td>Debt (LTV)</td><td>Equity</td><td>Monthly Rents</td><td>Annual NOI</td><td>UYOC</td></tr>
          </thead>
          <tbody>
            <tr><td>4777 35th st</td><td>3</td><td>1.49M</td><td>0.96M(62%)</td><td>0.58M</td><td>$11k</td><td>$91.4k</td><td>6.1%</td></tr>
            <tr><td>3322 Nile St</td><td>4</td><td>1.57M</td><td>1.05M (70%)</td><td>0.44M</td><td>$10.4k</td><td>$90.9k</td><td>5.8%</td></tr>
            <tr><td>4137 Louisiana St</td><td>12</td><td>4.12M</td><td>2.7M (62%)</td><td>1.65M</td><td>$30.5k</td><td>$275k</td><td>6.6%</td></tr>
            <tr><td><b>TOTAL</b></td><td><b>19</b></td><td><b>7.23M</b></td><td><b>4.71M (64%)</b></td><td><b>2.67M</b></td><td><b>$51.9k</b></td><td><b>$457.3k</b></td><td><b>6.3%</b></td></tr>
          </tbody>
          </table> 
          </div>   
          
          <ul>
          <li>Total project cost: $7.23M</li>  
          <li>Equity/debt: 2.67M / 4.71M (64%)</li>  
          <li>UYOC: 6.3%</li>  
          <li>Targeted Investor IRR: 16-18%</li>
          <li>Targeted Investor Equity Multiple: 2.3x</li>
          <li>No acquisition or disposition fee</li>
          <li>No AUM fee</li>
          </ul>                                
          <p><b>Backyard waterfall</b></p>        
          <ul>
            <li>Preferred Return of 8% (cumulative)</li> 
            <li>From 8%-15% return: 80% LP / 20% Backyard GP split</li>
            <li>15%+ returns: 70% LP / 30% Backyard GP split</li>
          </ul>          
          <h3>The Backyard-Home3 SPV</h3>
          <p>Home3 secured a $1M allocation as primary LP, to be invested via a Special Purpose Vehicle (the "SPV"). We are charging a 1.5% AUM fee to cover our legal and accounting costs. As a volume investor discount, we secured a 0.25% (TODO:VERIFY) discount on Backyard's waterfall via a side letter. The SPV has its own waterfall, which represents Home3's upside.</p>
          <p><b>SPV waterfall</b></p>        
          <ul>
            <li>Preferred Return of 8% (cumulative)</li> 
            <li>8%+ return: 80% SPV LP / 20% Home3 split</li>            
          </ul>  
        </article>  
        <article className="prose max-w-full mb-12">
          <h1>The Backyard Team</h1>
          <div className="grid lg:grid-cols-3 lg:gap-12">
            <div>
              <div className="avatar">
                <div className="w-36 rounded-full">
                  <img className="my-0" src="/images/coby.jpeg" />
                </div>                
              </div>
              <h3>Coby Lefkowitz</h3>
              <p><b>Ops, Underwriting, & Design</b></p>
              <p>Worked in real estate since 2015, including asset & property management, leasing, development, & acquisitions. Prolific writer and researcher on the built environment. </p>
            </div>
            <div>
              <div className="avatar">
                <div className="w-36 rounded-full">
                  <img className="my-0" src="/images/roee.jpeg" />
                </div>           
              </div>
              <h3>Roee Gold</h3>
              <p><b>Development & Construction</b></p>
            <p>Worked in real estate since 2015, including construction, property management, & development. Deep Roots in PropTech Community in Southern California</p>
            </div>
            <div>
            <div className="avatar">
              <div className="w-36 rounded-full">
                <img className="my-0" src="/images/gabe.jpeg" />
              </div>              
            </div>
            <h3>Gabriel Freifeld</h3>  
            <p><b>Finance & Investor Relations</b></p>
            <p>Worked in real estate since 2016, including acquisitions, financing, & funding deals. Deep Roots in real estate financing in Southern California & Mexico.</p>  
            </div>
          </div>       
          <p><i>Roee and Gabe at 4777 35th St, on Dec. 2022, during the Home3 dilligence trip</i></p>                          
          <img src="/images/RoeeAndGabe2.jpg" alt="Roee and Gabe from Backyard" />
          <p><i>As of March 16th, 4777 35th St is weeks aways from tenants.</i></p>                          
          <img src="/images/35th_complete_1.jpg" alt="35th st almost ready for tenants" />          
        </article>                 
        <article className="prose max-w-full"> 
          <h1>Deal Documents</h1>                          
          <p>
            <ul><li><a className="link link-hover" href="#">📄 Backyard Deal Overview</a></li>
            <li><a className="link link-hover" href="#">📄 Backyard 2022 Q3 Update</a></li>
            <li><a className="link link-hover" href="#">📄 Backyard-Home3 SPV Operating Agreement</a></li>
            <li><a className="link link-hover" href="#">📄 Backyard-Home3 SPV Side Letter</a></li>
            </ul>
          </p>          
          <h2>Next Steps</h2>
          <p>Reach out to marcio@home3.co with any questions about this deal.</p>
          <form action="https://forms.gle/o4uhhDWYWZAzzMSc6" method="get" target="_blank">
            <button className="btn btn-primar mb-12">Apply to invest</button>
          </form>      
        </article>        
      </div>
    </div>    
  )
}

