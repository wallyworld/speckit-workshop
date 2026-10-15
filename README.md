# Spec Kit Workshop

This project contains a workshop to introduce Spec Kit and illustrate
its use. There's also a new project template which can be used to seed
a new Spec Kit project.

- [The 90-minute workshop](index.md) - this is a hands-on introduction:
  the `specify -> plan -> tasks -> implement -> converge loop`, demoed
  on a pet store and practiced on an order-placement feature with a
  business rule which needs to be accounted for in the solution.
- [`new-project-template/`](new-project-template/) - a seedable project
  template - a requirements source, a roadmap, and requirement-phrase
  and digest checks. It's used to set up a fresh Spec Kit project.

To run the workshop: `./scripts/workshop.sh`, then `workshop shell` - it
runs inside a container the workshop CLI builds ([setup](01-setup.md)).
