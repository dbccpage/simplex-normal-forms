# Demo 02: Certificate Table Without Verifier

Status: Mechanization target.

A database table named `certificates` does not create authority.

Certification requires:

- packet well-formed
- evidence sufficient
- obstruction class computed
- terminal route declared
- certificate verifies

Authorization additionally requires:

- active authority verifier
- policy acceptance
- lineage/trust/scope acceptance

```text
CertifiedNF(x) does not imply AuthorizedNF(x).
```

Required rejection:

| Case | Required terminal |
|---|---|
| certificate row exists but no verifier replayed it | `Reject` or `Refuse` |
| metadata says authorized but policy verifier is missing | `Refuse` |
| verifier exists but scope is wrong | `Reject` |

A certificate table without a verifier is just another table.
