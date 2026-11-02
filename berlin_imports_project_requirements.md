# Berlin Imports --- Project Requirements

**Document type:** Product Requirements Document (PRD)\
**Version:** 1.0\
**Status:** Initial requirements for VS Code AI Agent implementation

## 1. Project Overview

Berlin Imports is an online automotive spare-parts store. Customers can
browse a catalogue, filter parts by vehicle make and category, view
product details, add products to a cart, and place orders through a
secure checkout and payment process.

The catalogue will primarily feature parts for **Mercedes-Benz, Audi,
BMW, and Porsche**. Brand logos may be displayed for navigation and
identification, subject to appropriate usage rights.

## 2. Project Goals

-   Provide a clear, responsive online shopping experience.
-   Make it easy to find parts by category, brand, vehicle
    compatibility, and search.
-   Support customer accounts, shopping carts, orders, and payment
    status tracking.
-   Give store staff/admins tools to manage products, inventory, orders,
    and customers.
-   Build a maintainable Django application using server-rendered Django
    templates and Tailwind CSS.

## 3. Technology Requirements

-   **Backend:** Python, Django
-   **Frontend:** Django Templates, HTML, Tailwind CSS, minimal
    JavaScript where useful
-   **Database:** PostgreSQL for production; SQLite may be used for
    local development
-   **Authentication:** Django authentication system
-   **Payments:** Integrate a payment provider through a documented
    adapter/service. Select the provider based on the deployment market
    (for example, M-Pesa for Kenya and/or a card provider such as Stripe
    where supported).
-   **Media:** Django media storage for product images; use cloud/object
    storage in production if required.
-   **Testing:** Django test framework or pytest
-   **Version control:** Git

Do not store card details or payment credentials in the application
database. Keep secrets in environment variables and provide an
`.env.example` file with placeholders only.

## 4. User Roles

### Guest

-   Browse, search, filter, and view products.
-   Add products to a session-based cart.
-   Register, log in, and proceed to checkout.

### Registered Customer

-   All guest capabilities.
-   Maintain profile and delivery details.
-   Checkout, pay, and view order history.
-   View order details and payment/order status.

### Store Administrator / Staff

-   Access Django admin and/or a protected staff dashboard.
-   Create, update, deactivate, and categorize products.
-   Manage product images, prices, stock levels, brand, and vehicle
    fitment.
-   View and manage orders, update fulfillment status, and review
    payment status.
-   Manage categories, brands, and customer records as permitted.

## 5. Functional Requirements

### 5.1 Storefront and Navigation

-   Create a polished, responsive storefront with Berlin Imports
    branding.
-   Include navigation for Home, Shop/Catalogue, Brands, Cart,
    Account/Login, and Orders (for signed-in customers).
-   Include a home page with featured products, popular categories, and
    brand links.
-   Provide responsive layouts for mobile, tablet, and desktop.
-   Show clear loading, empty, success, and error states.

### 5.2 Product Catalogue

-   Product categories must include at minimum:
    -   Engines
    -   Wheels
    -   Rims
    -   Engine control / autonomous engine system parts (confirm the
        intended product terminology with the business)
    -   Brake pads
-   Allow products to belong to a brand: Mercedes-Benz, Audi, BMW,
    Porsche, and additional brands configurable by staff.
-   Each product should support:
    -   Name and unique SKU/part number
    -   Brand and category
    -   Description and product images
    -   Price and currency
    -   Stock quantity and availability
    -   Vehicle compatibility details (make, model, year range,
        engine/trim where known)
    -   Optional condition (new/used/refurbished), warranty, and
        specifications
-   Catalogue features:
    -   Search by name, SKU, brand, and relevant fitment terms
    -   Filter by category, brand, price range, availability, and
        vehicle compatibility where data exists
    -   Sort by relevance, price, and newest
    -   Pagination
-   Product detail pages must show images, price, availability,
    specifications, compatibility, and an add-to-cart control.
-   Do not claim a part fits a vehicle unless compatibility data
    supports the claim.

### 5.3 Cart

-   Add a product to cart, change quantity, and remove an item.
-   Show product name, SKU, unit price, quantity, line total, and cart
    subtotal.
-   Validate requested quantity against available stock.
-   Persist guest carts in the session.
-   Associate or merge the guest cart with the customer cart after login
    where feasible.
-   Recalculate prices and stock on the server; do not trust totals sent
    by the browser.
-   Display an empty-cart state and a clear path back to the catalogue.

### 5.4 Authentication and Account

-   Customer registration, login, logout, and password reset.
-   Use Django's secure password handling and authentication features.
-   Validate email and required account fields.
-   Protect customer profile, order history, and checkout routes.
-   Customers must only access their own profile and orders.
-   Include profile editing and delivery/contact details.
-   Apply CSRF protection to all relevant forms.

### 5.5 Checkout and Orders

-   Checkout should collect/confirm customer name, email, phone,
    delivery address, and delivery method.
-   Display an order review including items, quantities, subtotal,
    delivery fee, discounts if enabled, and grand total.
-   Create an order with a unique order number and immutable
    purchase-line snapshots (product name/SKU, unit price, quantity).
-   Revalidate stock and price at checkout.
-   Define order states such as: `Pending Payment`, `Paid`,
    `Processing`, `Shipped`, `Delivered`, `Cancelled`, and `Refunded`
    (adjust transitions to the selected payment provider and business
    workflow).
-   Reduce or reserve stock safely to prevent overselling; define how
    unpaid/failed orders release reservations.
-   Send an order confirmation after successful order creation and
    payment confirmation.
-   Customers can view order history and order detail/status pages.
-   Staff can update fulfillment status and add tracking information
    where available.

### 5.6 Payments

-   Implement a payment service layer so the provider can be changed
    without rewriting checkout.
-   Start payment from checkout and show clear pending, success,
    failure, and cancellation outcomes.
-   Verify payment results server-side using the provider's
    callback/webhook and/or verification API.
-   Make webhook processing idempotent: duplicate callbacks must not
    duplicate payments, orders, or stock changes.
-   Store provider transaction/reference ID, amount, currency, status,
    and timestamps; never store sensitive card data.
-   Do not mark an order as paid based only on a browser redirect.
-   Support refunds or record refund status if the provider and business
    workflow allow it.
-   Keep payment credentials out of source control.
-   **Open business decision:** confirm payment provider(s), currency,
    delivery markets, and whether cash on delivery is required before
    implementing live payments. Use sandbox/test mode during
    development.

### 5.7 Inventory

-   Track stock quantity per product.
-   Prevent checkout for unavailable or insufficient stock.
-   Provide low-stock visibility for staff.
-   Record stock adjustments where practical.
-   Use database transactions and locking/atomic updates for checkout
    stock changes.

### 5.8 Notifications

-   Send transactional email for account/password reset, order
    confirmation, and relevant order status updates.
-   In development, use console email backend or another safe test
    backend.
-   In production, configure email through environment variables.
-   Payment SMS notifications are optional and should only be added if
    required.

### 5.9 Admin and Store Operations

-   Configure Django admin for brands, categories, products, inventory,
    orders, and payment records.
-   Restrict administrative actions to authorized staff.
-   Use validation and clear status labels.
-   Product deactivation should preserve historical order records.

### 5.10 SEO, Accessibility, and Usability

-   Use semantic HTML, accessible form labels, keyboard-friendly
    controls, and useful alt text.
-   Provide page titles, meta descriptions, clean URLs, and
    product-specific metadata.
-   Optimize product images and avoid unnecessarily large page payloads.
-   Use clear currency formatting and display the currency consistently.
-   Include privacy, terms, delivery/returns, and contact pages;
    business content can initially be placeholders approved by the
    owner.

## 6. Suggested Django App Structure

Use a modular structure. The AI agent may adjust names if it documents
the reason.

-   `config/` --- project settings, root URLs, ASGI/WSGI
-   `core/` --- home page, static pages, shared layout
-   `catalog/` --- brands, categories, products, vehicle fitment, search
-   `cart/` --- cart services and views
-   `accounts/` --- profiles and account-related views
-   `orders/` --- checkout, orders, order lines, fulfillment
-   `payments/` --- payment integration, callbacks/webhooks, transaction
    records
-   `inventory/` --- stock handling and adjustments (may be part of
    `catalog` if simpler)
-   `templates/` --- shared base and app templates
-   `static/` --- compiled Tailwind CSS and static assets

Use Django's built-in admin rather than building a custom admin
dashboard unless there is a clear requirement.

## 7. Initial Data Models (Conceptual)

-   **Brand:** name, slug, logo, active flag
-   **Category:** name, slug, description, parent category (optional)
-   **Product:** brand, category, name, SKU, slug, description, price,
    currency, stock, condition, active flag
-   **ProductImage:** product, image, alt text, sort order
-   **VehicleFitment:** product, make, model, year range, engine/trim
    details
-   **CustomerProfile:** user, phone, default delivery/contact details
-   **Cart / CartItem:** session or customer association, product,
    quantity
-   **Order:** customer (nullable for guest if enabled), order number,
    contact/delivery snapshot, totals, status, timestamps
-   **OrderItem:** order, product reference (nullable if product is
    later removed), product/SKU/name snapshot, unit price, quantity,
    line total
-   **Payment:** order, provider, provider reference, amount, currency,
    status, verification data/timestamps
-   **StockMovement (optional):** product, quantity change, reason,
    actor, timestamp

Use `Decimal` for monetary values. Add database constraints and indexes
for SKU, slugs, order numbers, and common catalogue filters.

## 8. Security and Quality Requirements

-   Use Django production security settings, secure cookies/HTTPS in
    production, and correct `ALLOWED_HOSTS`.
-   Protect forms with CSRF and validate all user input server-side.
-   Enforce authorization for staff actions and customer-owned records.
-   Avoid exposing secrets, payment tokens, or sensitive personal
    information in logs.
-   Use Django ORM safely; avoid raw SQL unless justified.
-   Add tests for authentication, catalogue, cart, checkout, inventory,
    payment callbacks, and authorization.
-   Include useful error handling and logging without exposing internal
    tracebacks to customers.
-   Keep dependencies pinned or managed in a requirements file.
-   Add database migrations and ensure a clean setup works from
    documented instructions.

## 9. UI Direction

-   Brand name: **Berlin Imports**
-   Style: modern automotive parts retailer; clean, premium, practical,
    and trustworthy.
-   Use brand logos in the brands section and product/catalogue context.
    Only use logos/assets the business is allowed to use.
-   Design shared components: header, footer, product card, brand tile,
    filters, quantity selector, cart summary, form fields, alerts, and
    pagination.
-   Use Tailwind CSS consistently. Avoid adding a second CSS framework.
-   Do not overuse animations; prioritize product discovery and checkout
    clarity.
-   Use placeholder images only during development and label them as
    placeholders.

## 10. Required Pages

1.  Home
2.  Catalogue / Shop
3.  Category results
4.  Brand results
5.  Product detail
6.  Search results
7.  Cart
8.  Checkout
9.  Payment result (pending/success/failure)
10. Register
11. Login
12. Password reset flow
13. Customer profile
14. Customer order history
15. Order detail
16. About Berlin Imports
17. Contact
18. Delivery, Returns, Privacy Policy, and Terms
19. Staff/Django admin

## 11. Acceptance Criteria

The project is considered ready for an initial release when: - A visitor
can browse and search products, filter by brand/category, and open
product details. - A visitor can add items to a cart and update/remove
quantities. - Registration, login, logout, and password reset work. -
Checkout creates an order with correct server-calculated totals and
purchase snapshots. - Insufficient stock is rejected and concurrent
checkout cannot oversell inventory. - Payment success is confirmed
server-side; failed/pending payments are represented accurately. -
Duplicate payment callbacks do not duplicate financial or inventory
actions. - A customer can view only their own orders. - Staff can manage
products, brands, categories, inventory, and fulfillment. - Main pages
are responsive and usable on mobile and desktop. - Automated tests cover
critical flows, and setup instructions work on a clean environment.

## 12. Development Plan for the VS Code AI Agent

Work in small, reviewable phases. Do not attempt to generate the entire
application in one pass.

### Phase 1 --- Project foundation

-   Inspect the repository and report existing structure before changing
    files.
-   Create the Django project and apps, settings, URL configuration,
    base template, and Tailwind setup.
-   Add `.env.example`, `.gitignore`, dependency file, and README setup
    instructions.
-   Verify the project starts and tests run.

### Phase 2 --- Catalogue

-   Implement Brand, Category, Product, ProductImage, and VehicleFitment
    models.
-   Add admin configuration, migrations, sample fixture/seed data,
    catalogue views, search, filters, and product detail templates.
-   Add tests and verify.

### Phase 3 --- Accounts and cart

-   Implement registration/login/logout/password reset/profile.
-   Implement session cart and cart operations with server-side
    validation.
-   Add tests and verify.

### Phase 4 --- Orders and checkout

-   Implement checkout, order snapshots, order states, stock validation,
    and safe stock updates.
-   Add order history/detail pages and staff workflow.
-   Add tests and verify.

### Phase 5 --- Payments

-   Confirm provider and market requirements with the project owner
    before selecting live payment configuration.
-   Implement sandbox integration, server-side verification, webhook
    idempotency, and payment result pages.
-   Add tests using mocked provider responses. Never use real
    credentials in development.

### Phase 6 --- Polish and release readiness

-   Complete responsive styling, accessibility, SEO basics,
    notifications, policy pages, and error states.
-   Run tests, lint/format checks if configured, and security checks.
-   Document deployment, environment variables, database migration,
    static/media handling, backups, and payment webhook setup.
-   Provide a concise completion report: files created, features
    implemented, commands run, test results, known gaps, and decisions
    requiring owner input.

## 13. AI Agent Operating Rules

-   First inspect the existing codebase and identify its
    framework/version and current state. Do not overwrite an existing
    project blindly.
-   Treat this document as requirements, not permission to invent
    business decisions.
-   Ask before making irreversible changes, deleting data, deploying, or
    enabling live payments.
-   Do not place secrets or real customer/payment data in source code,
    fixtures, screenshots, or logs.
-   Prefer Django conventions and straightforward maintainable code over
    unnecessary abstractions.
-   Implement one phase at a time. After each phase, summarize changes
    and run relevant checks.
-   If requirements conflict or an important detail is missing, stop and
    ask a focused question rather than guessing.
-   Do not claim a feature or test is complete unless it has actually
    been implemented or run.
-   Keep templates, forms, views, and business logic organized; put
    critical cart, order, inventory, and payment rules in server-side
    services/models rather than only in templates or JavaScript.

## 14. Open Questions for the Project Owner

These decisions should be clarified before production checkout: 1. Which
payment methods are required: M-Pesa, card, bank transfer, cash on
delivery, or a combination? 2. What currency/currencies should be used
(for example, KES, EUR, or USD)? 3. Which countries/regions will Berlin
Imports deliver to? 4. Are parts new, used, refurbished, or mixed? 5. Is
vehicle fitment data available, or will staff enter it manually? 6.
Should customers be allowed to checkout as guests, or must they create
an account? 7. What delivery pricing and returns/warranty policies
apply? 8. Is there an existing logo, brand palette, domain, or product
dataset to use?

## 15. Definition of Done for Each Agent Task

-   The implementation matches the stated requirement.
-   Relevant migrations are created.
-   Relevant automated tests are added and pass.
-   Templates have responsive and empty/error states.
-   No secrets are committed.
-   The agent reports what changed and how to verify it.
