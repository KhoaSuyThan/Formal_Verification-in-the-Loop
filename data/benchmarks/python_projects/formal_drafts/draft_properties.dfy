// REVIEW DRAFT ONLY. These predicates describe proposed behavior of abstract
// snapshots. They do not verify a Python patch or establish Python/Dafny
// correspondence. No manifest includes this file as a scored formal task.

module DraftDjango10554 {
  datatype QuerySnapshot = QuerySnapshot(ids: seq<int>, orderKeys: seq<int>)

  // Evaluating the derived union must not change the original query object.
  predicate OriginalUnionStable(before: QuerySnapshot, after: QuerySnapshot,
                                derivedIds: seq<int>) {
    before == after &&
    multiset(derivedIds) == multiset(before.ids)
  }
}

module DraftDjango11400 {
  function EffectiveOrdering(adminOrdering: seq<string>,
                             metaOrdering: seq<string>): seq<string> {
    if |adminOrdering| > 0 then adminOrdering else metaOrdering
  }

  // orderRank abstracts a database order for the selected ordering policy.
  predicate RelatedChoicesOrdered(eligibleIds: seq<int>, choices: seq<int>,
                                  orderRank: map<int, int>) {
    multiset(choices) == multiset(eligibleIds) &&
    (forall id :: id in choices ==> id in orderRank) &&
    (forall i | 0 <= i < |choices| - 1 ::
      orderRank[choices[i]] <= orderRank[choices[i + 1]])
  }
}

module DraftXarray2905 {
  // objectId models Python identity; valuesPropertyId is deliberately unused.
  predicate ScalarObjectAssignment(objectId: int, valuesPropertyId: int,
                                   storedObjectId: int, resultDtype: string) {
    storedObjectId == objectId && resultDtype == "object"
  }
}

module DraftXarray3095 {
  datatype IndexSnapshot = IndexSnapshot(values: seq<string>, dtype: string,
                                         storageId: int)

  predicate UnicodeIndexCopyPreserved(before: IndexSnapshot,
                                      after: IndexSnapshot, deep: bool) {
    before.values == after.values &&
    before.dtype == after.dtype &&
    (deep ==> before.storageId != after.storageId)
  }
}

module DraftXarray3305 {
  predicate QuantileAttributes(before: map<string, string>,
                               after: map<string, string>, keepAttrs: bool) {
    keepAttrs ==> after == before
  }
}

module DraftXarray4687 {
  predicate WhereAttributes(before: map<string, string>,
                            after: map<string, string>, keepAttrs: bool) {
    keepAttrs ==> after == before
  }
}

module DraftXarray6938 {
  datatype DatasetSnapshot = DatasetSnapshot(
    variableDims: map<string, seq<string>>,
    values: map<string, seq<int>>,
    coords: set<string>)

  predicate SwapDimsLeavesInputUnchanged(before: DatasetSnapshot,
                                         after: DatasetSnapshot) {
    after == before
  }
}

module DraftXarray6992 {
  // Coordinate names may contain names not present in variables.
  predicate DataVariablesConsistent(variables: map<string, int>,
                                    coordinateNames: set<string>,
                                    returnedNames: set<string>,
                                    reportedCount: int) {
    returnedNames == variables.Keys - coordinateNames &&
    reportedCount == |returnedNames|
  }
}

module DraftXarray7393 {
  predicate StackedCoordinateDtype(beforeDtype: string, afterDtype: string) {
    beforeDtype == "int32" ==> afterDtype == "int32"
  }
}

module DraftSphinx7462 {
  // The exact rendering is deliberately open for reviewer confirmation.
  predicate EmptyTupleAnnotationSafe(rendered: string, raisedIndexError: bool) {
    !raisedIndexError && |rendered| > 0
  }
}
