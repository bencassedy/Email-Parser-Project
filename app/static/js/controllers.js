esApp.controller('SearchCtrl', ['$scope', '$filter', 'es', 'TagService', 'ResultService', function($scope, $filter, es, TagService, ResultService) {
    es.cluster.health(function (err, resp) {
        if (err) {
            $scope.data = err.message;
        } else {
            $scope.data = resp;
        }
    });

    // populate select drop-down with email metadata choices, defaults to email body
    $scope.fieldSelect = 'body';

    es.indices.getMapping({index:'enron', type:'email'}, function(err, resp) {
        if (err) {
            $scope.fields = err.message;
        } else {
            $scope.fields = Object.keys(resp.enron.mappings.email.properties);
        }
    });

    // execute standard boolean-style search query
    $scope.search = function() {
        // elasticsearch will return an error if the query string ends with whitespace,
        // so we'll put in some conditional handling of the query string before sending to ES
        var queryTerm;
        if (!$scope.queryTerm) {
            queryTerm = '*';
        } else {
            if ($scope.queryTerm.substr(-1) === ' '){
                queryTerm = $scope.queryTerm.trim();
            } else {
                queryTerm = $scope.queryTerm;
            }
        }

        es.search({
            index: 'enron',
            size: 200,
            body: {
                query: {
                    query_string: {
                        default_field: $scope.fieldSelect, 
                        query: queryTerm
                    }
                },
                highlight: {
                    pre_tags: ["<mark>"],
                    post_tags: ["</mark>"],
                    fields: {
                        body: {}
                    }
                }
            }
        }).then(function (resp) {   
            $scope.results = resp.hits.hits;
            $scope.hitCount = resp.hits.total;
            }, function (err) {
        });
    };

    $scope.getSelectedResults = function() {
        $scope.selectedResults = $filter('filter')($scope.results, {selected: true});
        $scope.selectedResultIDs = [];
        angular.forEach($scope.selectedResults, function(doc) {
            $scope.selectedResultIDs.push(doc._id);
        });
        ResultService.sharedResults = $scope.selectedResultIDs;
    };

    // execute more-like-this search with multiple docs as input
    $scope.mltSearch = function() {
        $scope.results = [];
        $scope.hitCount = 0;
        angular.forEach($scope.selectedResultIDs, function(value) {
            es.mlt({
                index: 'enron',
                type: 'email',
                id: value,
                mlt_fields: 'body',
                minDocFreq: 1,
                minTermFreq: 1,
                percentTermsToMatch: 0.9,
                searchSize: 200
            }).then(function (resp) {   
                $scope.results = $scope.results.concat(resp.hits.hits);
                $scope.hitCount += resp.hits.total;
                }, function (err) {
            });
        });
    };
    
    //execute multiple searches in same text box to get hit count reports for each search
    $scope.multiSearchArray = [];
    $scope.multiSearchArrayResults = [];
    
    $scope.multiSearch = function() {
        angular.forEach($scope.multiSearchArray, function(value) {
            es.search({
                index: 'enron',
                body: {
                    filter: {
                        query: {
                            query_string: {
                                query: value,
                                default_operator: "AND"
                            }
                        }
                    }
                },
                searchType: "count"
            }).then(function(resp) {
                $scope.multiSearchArrayResults.push({term: value, hits: resp.hits.total});
            }, function(err) {
                $scope.multiSearchArrayResults.push({term: value, hits: err});
            });
        });
    };

    
    // master checkbox toggles all checkboxes
    $scope.master = false;
    $scope.onMasterChange = function() {
         for (var i = 0; i < $scope.results.length; i++) {
             $scope.results[i].selected = $scope.master;
         }
    };
    
    $scope.change = function() {
        for (var i = 0; i < $scope.results.length; i++) {
            if($scope.master == true){
                $scope.results[i].selected = $scope.master;
            }
        }
    };

    $scope.sharedTags = TagService;

    angular.element(document).ready(function () {
        $scope.search();
    });

    $scope.predicate = '';
}]);


// this controller handles CRUD-style requests for document tagging going to and from Mongo
esApp.controller('TagCtrl', ['$scope', '$http', '$window', '$filter', 'TagService', 'ResultService', function($scope, $http, $window, $filter, TagService, ResultService) {

    // get list and populate select boxes with existing tags in tag db collection
    $scope.getTags = function() {
        $http
            .get('/tags')
            .success(function(data, status) {
                $scope.tags = data;
                $scope.status = status;
            })
            .error(function(data, status) {
                $scope.tags = data || "Request failed";
                $scope.status = status;
            });
        return $scope.tags;
    };

    // add tag to tag db collection
    $scope.addTag = function() {
        $http
            .post('/tags', {
                name: $scope.tagValue
            })
            .success(function(data, status, headers, config) {
                if (data.success) {
                    $scope.tagSuccess = true;
                } else {
                    $window.alert('Adding of tag failed');
                }
            })
            .error(function(data, status, headers, config) {
            });

        $scope.tags.push({name: $scope.tagValue});
        $scope.tagValue = '';
        return $scope.tags;
    };

    // send list of selected tags over http to do CRUD operations
    $scope.getSelectedTags = function() {
        $scope.selectedTags = $filter('filter')($scope.tags, {selected: true});
        TagService.sharedTags = $scope.selectedTags;
        $scope.selectedTagNames = [];
        angular.forEach($scope.selectedTags, function(tag) {
            angular.forEach(tag, function(value, key) {
                if (key === 'name') {
                    $scope.selectedTagNames.push(" " + value);
                }
            });
        });
    };

    // delete tag from tag collection
    $scope.deleteMessage = "Are you sure you want to delete the following tags? ";
    
    $scope.deleteTags = function(deleteMessage) {
        $scope.getSelectedTags();
        var okDelete = $window.confirm($scope.deleteMessage + $scope.selectedTagNames);
        if (okDelete) {
            $http
                .post('/tags_delete', $scope.selectedTags)
                .success(function(data, status, headers, config) {
                    if (data.success) {
                        $window.alert("Deletion of tags succeeded");
                        $scope.getTags();
                    } else {
                        $window.alert("Deletion of tags failed");
                    }
                })
                .error(function(data, status, headers, config) {

            });
        }
    };

    // get selected results from search controller for applying tags to records
    $scope.selectedResultIDs = ResultService;
}]);

// directives

// esApp.directive('checkboxAll', function () {
//   return function(scope, iElement, iAttrs) {
//     var parts = iAttrs.checkboxAll.split('.');
    
//     //var masterCb = $element.children()[0];
    
//     iElement.attr('type','checkbox');
//     iElement.bind('change', function (evt) {
//       scope.$apply(function () {
//         var setValue = iElement.prop('checked');
//         angular.forEach(scope.$eval(parts[0]), function (v) {
//           v[parts[1]] = setValue;
//         });
//       });
//     });
//     scope.$watch(parts[0], function (newVal) {
//       var hasTrue, hasFalse;
//       angular.forEach(newVal, function (v) {
//         if (v[parts[1]]) {
//           hasTrue = true;
//         } else {
//           hasFalse = true;
//         }
//       });
//       if (hasTrue && hasFalse) {
//         iElement.attr('checked', false);
//         iElement.addClass('greyed');
       
//       } else {
//         iElement.attr('checked', hasTrue);
//         iElement.removeClass('greyed');
     
//       }
//     }, true);
//   };
// });
