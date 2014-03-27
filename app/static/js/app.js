// root-level module that talks to angular using ng-app directive

var esApp = angular.module('esApp', ['elasticsearch', 'ngSanitize']);

esApp.factory('es', ['esFactory', function(esFactory) {
	return esFactory({
		host: 'localhost:9200'
	});
}]);
