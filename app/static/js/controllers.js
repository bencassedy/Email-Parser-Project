esApp.controller('SearchCtrl', ['$scope', '$filter', 'es', function($scope, $filter, es) {
    es.cluster.health(function (err, resp) {
        if (err) {
            $scope.data = err.message;
        } else {
            $scope.data = resp;
        }
    });


    // $scope.toggleSuggester = function() {
    //     if ($scope.queryTerm == '') {
    //         $('p').hide();
    //     } else {
    //         $('p').show();
    //     }
    // };


// populate select drop-down with email metadata choices, defaults to email body

    $scope.fieldSelect = 'body';

    es.indices.getMapping({index:'test_kaminski', type:'email'}, function(err, resp) {
        if (err) {
            $scope.fields = err.message;
        } else {
            $scope.fields = Object.keys(resp.email.properties);
        }
    });


// execute standard boolean-style search query

    $scope.search = function() {
        es.search({
            index: 'test_kaminski',
            size: 200,
            suggestText: ($scope.queryTerm || ''),
            body: {
                query: {
                    query_string: {
                        default_field: $scope.fieldSelect, 
                        query: ($scope.queryTerm || '*')
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
                $scope.results(err.message);
        });
        // es.suggest({ // is not working with completion suggester, only works with term suggester. Need to change mappings/settings
        //     index: 'test_kaminski',
        //     suggestMode: 'popular',
        //     body: {
        //         mysuggester: {
        //             text: ($scope.queryTerm || ''),
        //             term: {
        //                 field: 'body',
        //                 suggest_mode: 'always'
        //             }
        //         }
        //     }
        // }).then(function(response) {
        //     $scope.suggestResults = response;
        // }, function(error) {
        //     $scope.suggestResults = error.message;
        // })
    };


    
    $scope.getSelectedResults = function() {
        $scope.selectedResults = $filter('filter')($scope.results, {selected: true});
        $scope.selectedResultIDs = [];
        angular.forEach($scope.selectedResults, function(doc) {
            $scope.selectedResultIDs.push(doc._id);
        });
    };

// execute more-like-this search with multiple docs as input

    $scope.mltSearch = function() {
        $scope.results = [];
        $scope.hitCount = 0;
        angular.forEach($scope.selectedResultIDs, function(value) {
            es.mlt({
                index: 'test_kaminski',
                type: 'email',
                id: value,
                mlt_fields: 'body',
                // minDocFreq; 1, // results in error
                minTermFreq: 1,
                percentTermsToMatch: 0.8,
                searchSize: 200
            }).then(function (resp) {   
                $scope.results = $scope.results.concat(resp.hits.hits);
                $scope.hitCount += resp.hits.total;
                }, function (err) {
                    $scope.results(err.message);
            });
        });
    };
    
//execute multiple searches in same text box to get hit count reports for all searches
    
    $scope.multiSearchArray = [];
    $scope.multiSearchArrayResults = [];
    
    $scope.multisearch = function() {
        angular.forEach($scope.multiSearchArray, function(value) {
            es.count({
                index: 'test_kaminski',
                body: {
                    term: {
                        _all: value
                    }
                }
            }).then(function(resp) {
                $scope.multiSearchArrayResults.push({term: value, hits: resp.count});
            }, function(err) {
                $scope.multiSearchArrayResults.push({term: value, hits: err});
            });
        });
    };


    angular.element(document).ready(function () {
      $scope.search();
    });

    $scope.predicate = '';
}]);


// this controller handles CRUD-style requests for document tagging going to and from Mongo

esApp.controller('TagCtrl', ['$scope', '$http', '$window', '$filter', function($scope, $http, $window, $filter) {


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
        $scope.selectedTagNames = [];
        angular.forEach($scope.selectedTags, function(tag) {
            angular.forEach(tag, function(value, key) {
                if (key === 'name') {
                    $scope.selectedTagNames.push(" " + value);
                }
            });
        });
    };


// delete tag from tagging db collection

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
        };
    };
}]);
