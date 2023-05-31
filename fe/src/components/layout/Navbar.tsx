import * as React from "react"
import { Fragment } from "react"
import { Disclosure, Menu, Transition } from "@headlessui/react"
import { MenuIcon, XIcon } from "@heroicons/react/outline"
import { IoPersonCircleOutline } from "react-icons/io5"
import { Link, NavLink } from "react-router-dom"
import Home3Logo from "./Home3Logo"
import { useAuth } from "../../hooks/Auth"

const mockUser = {
  name: "Tom Cook",
  email: "tom@example.com",
  imageUrl:
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
}

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ")
}

const navigation = [
  { name: "Map", href: "/map", current: false },
  { name: "Properties", href: "/properties", current: false },
  { name: "Listings", href: "/listings", current: false },
  { name: "Search", href: "/search", current: false },
  { name: "Rental Rates", href: "/rental-rates", current: false },
  // { name: 'Debug', href: routes.debug(), current: false },
]
const userNavigation = [
  { name: "Profile", href: "#" },
  // { name: 'Settings', href: '#' },
  { name: "Sign out", backend_href: "/user/logout" },
]

function mobileMenu({ isAuthenticated, user }: { isAuthenticated: boolean, user: any }) {
  return (
    <nav className="mx-auto md:hidden w-100">
      <div className="w-100">
        {/* mobile menu items */}
        <Disclosure as="div" className="md:hidden w-100">
          {/* Mobile menu hamburger button */}
          {({ open }) => (<>
              {/* Hamburger menu icon: */}
              <div className="-mr-2 flex md:hidden justify-between w-100">
                <Disclosure.Button
                  className="bg-gray-800 inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white">
                  <span className="sr-only">Open main menu</span>
                  {open ? (
                    <XIcon className="block h-6 w-6" aria-hidden="true"/>
                  ) : (
                    <MenuIcon className="block h-6 w-6" aria-hidden="true"/>
                  )}
                </Disclosure.Button>
                <div className="pt-1">
                  <Link to="/" >
                    <Home3Logo/>
                  </Link>
                </div>
              </div>
              {/* Logo:*/}

              {/* menu contents: */}
              <Disclosure.Panel>
                <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                  {navigation.map((item) => (
                    <Disclosure.Button
                      key={item.name}
                      as="a"
                      href={item.href}
                      className={classNames(
                        item.current
                          ? "bg-gray-900 text-white" : "hover:bg-gray-700 hover:text-white",
                        "block px-3 py-2 rounded-md text-base font-medium"
                      )}
                      aria-current={item.current ? "page" : undefined}
                    >
                      {item.name}
                    </Disclosure.Button>
                  ))}
                </div>
                <div className="pt-4 pb-3 border-t border-gray-700">
                  {isAuthenticated && (
                    // user name and profile pic
                    <div className="flex items-center px-5">
                      <div className="flex-shrink-0">
                        <img className="h-10 w-10 rounded-full" src={mockUser.imageUrl} alt=""/>
                      </div>
                      <div className="ml-3">
                        <div className="text-base font-medium leading-none text-white">{user.first_name}</div>
                        <div className="text-sm font-medium leading-none text-gray-400">{user.email}</div>
                      </div>
                    </div>
                  )}
                  {isAuthenticated && (
                    // user settings and logout button
                    <div className="mt-3 px-2 space-y-1">
                      {userNavigation.map((item) => (
                        <Disclosure.Button
                          key={item.name}
                          as="a"
                          href={item.href}
                          className="block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-gray-700"
                        >
                          {item.name}
                        </Disclosure.Button>
                      ))}
                    </div>
                  )}
                </div>
              </Disclosure.Panel>
            </>
          )}
        </Disclosure>
      </div>
    </nav>
  )
}

function desktopMenu({ isAuthenticated, user }: { isAuthenticated: boolean, user: any }) {
  return (
    <nav className="mx-auto hidden md:block">
      <div className="flex items-center justify-between h-16">
        <div className="flex items-center">
          {/* Logo:*/}
          <Link to="/">
            <Home3Logo/>
          </Link>
          {/* desktop menu items */}
          <div>
            <div className="ml-10 flex items-baseline space-x-4">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    (isActive ? "bg-gray-100" : "hover:bg-gray-300") +
                    " px-3 py-2 rounded-md text-sm font-medium"
                  }
                >
                  {item.name}
                </NavLink>
              ))}
            </div>
          </div>
        </div>

        {/* Desktop - Profile dropdown */}
        <div className="hidden md:block">
          <div className="ml-4 md:ml-6 flex items-center">

            {!isAuthenticated && <span>No auth</span>}
            {isAuthenticated && <span className="text-sm text-gray-700">{user.email}</span>}
            {isAuthenticated && (
              // this uses https://headlessui.dev/react/menu Menu
              <Menu as="div" className="ml-3 flex items-center flex-col justify-items-center relative">
                <Menu.Button className="flex-none">
                  <span className="sr-only">Open user menu</span>
                  <IoPersonCircleOutline size="28px"/>
                </Menu.Button>
                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  {/* Dropdown menu for user avatar icon.*/}
                  <Menu.Items
                    className="origin-top-right absolute right-1 top-1 z-40 mt-7 w-36 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none">
                    {userNavigation.map((item) => (
                      <Menu.Item key={item.name}>
                        {({ active }) => {
                          const classnames = classNames(
                            active ? "bg-gray-100" : "",
                            "block px-4 py-2 text-sm text-gray-700"
                          )
                          if (item?.backend_href) {
                            return (
                              <a href={item.backend_href} className={classnames}>
                                {item.name}
                              </a>
                            )
                          } else {
                            return (
                              <Link to={item.href as string} className={classnames}>
                                {item.name}
                              </Link>
                            )
                          }
                        }}
                      </Menu.Item>
                    ))}
                  </Menu.Items>
                </Transition>
              </Menu>
            )}
          </div>
        </div>
      </div>
    </nav>
  )

}

export default function Navbar() {
  const { user } = useAuth()
  const isAuthenticated = !!user

  return (
    <>
      <div className="h-1 w-full bg-acc"></div>
      <div className="md:container px-8 lg:px-16 py-2 mx-auto">
        {desktopMenu({ isAuthenticated, user })}
        {mobileMenu({ isAuthenticated, user })}
      </div>
    </>
  )
}
