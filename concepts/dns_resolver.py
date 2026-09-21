
import dns.resolver

print("1. Script started")
print("2. dns.resolver imported successfully")


def check_dns_records(domain):
    print(f"3. Entered check_dns_records() with: {domain}")

    print("4. Trying A record...")
    try:
        answers = dns.resolver.resolve(domain, "A")
        print("5. A record DNS query completed")

        for rdata in answers:
            print(f"A record: {rdata.address}")

    except Exception as e:
        print(f"ERROR in A record: {type(e).__name__}: {e}")
    
    answers = dns.resolver.resolve(domain, "A")
    print(f"TTL: {answers.rrset.ttl} seconds")

    print("6. Trying CNAME record...")
    try:
        answers = dns.resolver.resolve(domain, "CNAME")
        print("7. CNAME DNS query completed")

        for rdata in answers:
            print(f"CNAME record: {rdata.target}")

    except Exception as e:
        print(f"ERROR in CNAME record: {type(e).__name__}: {e}")

    print("8. Trying NS record...")
    try:
        answers = dns.resolver.resolve(domain, "NS")
        print("9. NS DNS query completed")

        for rdata in answers:
            print(f"NS record: {rdata.target}")

    except Exception as e:
        print(f"ERROR in NS record: {type(e).__name__}: {e}")

    print("10. Function completed")


print("11. About to call check_dns_records()")

check_dns_records("www.zappos.com")



domains = [
            "www.zappos.com",
        "www.example.com",
    ]

# for d in domains:
#     check_dns_records(d)

print("12. Script completed")