# Owner pricing — 21 October 2026 review

Owner-selected pricing for the new booking service. This is review copy, not a deployed contract or an activated charging system.

## Customer-facing owner copy

**£49 annual advertising fee per vehicle, plus a £25 admin fee per confirmed booking.**

Advertise your caravan, motorhome or campervan for 12 months. A flat £25 booking admin fee helps cover the administration of each confirmed booking. No automatic annual renewal.

The £25 is funded from the owner's £250 booking deposit when the full balance is confirmed paid or 12 weeks before arrival, whichever comes first. After the admin fee, £225 of that deposit remains with the owner. An enquiry or temporary date hold does not incur the booking fee.

## Integration requirements

- Save the accepted plan version and agreed amounts against the owner/booking. The policy helper supplies £49 annual and £25 booking amounts; it does not establish acceptance or charge money.
- Existing £49/no-commission advertising agreements keep their recorded terms until a new agreement is explicitly accepted. The existing garage builder and public terms describe that legacy advertising-only service. Replace them together with the new booking workflow, rather than mix the two services.
- The new service needs owner payment confirmations, audit history, booking confirmation through Touring, and customer-detail release only after balance confirmation. These are not yet wired into Owner's Garage.
- Keep the £250 booking deposit separate from any refundable damage/security deposit. Cancellation/refund terms, the transition date and owner acceptance flow still need completing before launch.
- Use “booking admin fee” in public wording. The internal `commission()` function retains its name for compatibility; it takes the recorded agreed amount and uses the earlier balance/12-week trigger. This fee is an owner charge, not an extra hirer checkout charge.
