import fs from "node:fs";
import clingo from "clingo-wasm";

const fixture = JSON.parse(
  fs.readFileSync(new URL("../../tests/fixtures/placement_parity.json", import.meta.url))
);
const program =
  fs.readFileSync(new URL("../../asp/KeyItemSolvingShip.lp", import.meta.url), "utf8") +
  "\n" +
  fs.readFileSync(new URL("../../asp/KeyItemDataShip.lp", import.meta.url), "utf8");

if (fixture.configuration !== "frumpy" || fixture.sign_def !== "rnd" || fixture.models !== 1) {
  throw new Error("Unexpected solver configuration in placement fixture");
}

function comparePair(a, b) {
  if (a[0] !== b[0]) return a[0] < b[0] ? -1 : 1;
  if (a[1] !== b[1]) return a[1] < b[1] ? -1 : 1;
  return 0;
}

function parsePairs(witness) {
  const pairs = [];
  for (const value of witness) {
    const match = /^pair\(([^,]+),([^)]+)\)$/.exec(value);
    if (match) {
      pairs.push([match[1], match[2]]);
    } else if (value.startsWith("notHas(")) {
      throw new Error(`Invalid placement model: ${value}`);
    }
  }
  return pairs.sort(comparePair);
}

let failures = 0;
const seeds = Object.keys(fixture.seeds);
for (const seed of seeds) {
  const result = await clingo.run(program, fixture.models, [
    `--configuration=${fixture.configuration}`,
    `--seed=${seed}`,
    `--sign-def=${fixture.sign_def}`,
  ]);

  if (result.Result !== "SATISFIABLE") {
    console.error(`seed ${seed}: ${result.Result ?? result.Error}`);
    failures += 1;
    continue;
  }

  const witness = result.Call?.[0]?.Witnesses?.[0]?.Value ?? [];
  const actual = parsePairs(witness);
  const expected = fixture.seeds[seed].map((pair) => [pair[0], pair[1]]).sort(comparePair);

  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    failures += 1;
    console.error(`seed ${seed}: placement mismatch`);
    if (failures === 1) {
      console.error("expected:", JSON.stringify(expected));
      console.error("actual:  ", JSON.stringify(actual));
    }
  }
}

if (failures > 0) {
  console.error(`${failures}/${seeds.length} placement vectors failed`);
  process.exit(1);
}

console.log(`${seeds.length} placement vectors matched native clingo`);
