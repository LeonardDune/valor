// Constraints
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS NODE KEY;
CREATE CONSTRAINT thread_id IF NOT EXISTS FOR (t:ConversationThread) REQUIRE t.id IS NODE KEY;
CREATE CONSTRAINT org_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS NODE KEY;
CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS NODE KEY;
CREATE CONSTRAINT space_id IF NOT EXISTS FOR (s:Space) REQUIRE s.id IS NODE KEY;

// Base Entity Constraints (Identity)
CREATE CONSTRAINT theme_base_id IF NOT EXISTS FOR (t:ThemeBase) REQUIRE t.id IS NODE KEY;
CREATE CONSTRAINT factor_base_id IF NOT EXISTS FOR (f:FactorBase) REQUIRE f.id IS NODE KEY;
CREATE CONSTRAINT claim_base_id IF NOT EXISTS FOR (c:ClaimBase) REQUIRE c.id IS NODE KEY;

// Version Entity Constraints (State)
CREATE CONSTRAINT theme_version_id IF NOT EXISTS FOR (v:ThemeVersion) REQUIRE v.id IS NODE KEY;
CREATE CONSTRAINT factor_version_id IF NOT EXISTS FOR (v:FactorVersion) REQUIRE v.id IS NODE KEY;
CREATE CONSTRAINT claim_version_id IF NOT EXISTS FOR (v:ClaimVersion) REQUIRE v.id IS NODE KEY;

// Decision Constraints
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS NODE KEY;

// Indexes
CREATE INDEX factor_version_name IF NOT EXISTS FOR (f:FactorVersion) ON (f.name);
CREATE FULLTEXT INDEX claim_version_text IF NOT EXISTS FOR (c:ClaimVersion) ON EACH [c.statement];
CREATE INDEX decision_timestamp IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);

// Legacy Constraints (Optional: keep if needed for rollback, but we wiped data)
// CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS NODE KEY;
// CREATE CONSTRAINT factor_id IF NOT EXISTS FOR (f:Factor) REQUIRE f.id IS NODE KEY;
// CREATE CONSTRAINT theme_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.id IS NODE KEY;
