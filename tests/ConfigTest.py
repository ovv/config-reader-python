import os
import json
import base64
import unittest


class ConfigTest(unittest.TestCase):

    """

    ..todo:: Figure out Config() import statement
    ..todo:: Test buildtime properties magic methods work?? (__get__)
    """

    # A mock environment to simulate build time.
    mockEnvironmentBuild = []

    # A mock environment to simulate runtime.
    mockEnvironmentDeploy = []

    def runTest(self):
        pass

    def setUp(self):

        env = self.loadJsonFile('ENV')

        for item in ['PLATFORM_APPLICATION', 'PLATFORM_VARIABLES']:

            env[item] = self.encode(self.loadJsonFile(item))

        self.mockEnvironmentBuild = env

        # These sub-values are always encoded

        for item in ['PLATFORM_ROUTES', 'PLATFORM_RELATIONSHIPS']:

            env[item] = self.encode(self.loadJsonFile(item))

        env_runtime = self.loadJsonFile('ENV_runtime')

        env = self.array_merge(env, env_runtime)

        self.mockEnvironmentDeploy = env

    @staticmethod
    def array_merge(first_array, second_array):

        if isinstance(first_array, list) and isinstance(second_array, list):
            return first_array + second_array

        elif isinstance(first_array, dict) and isinstance(second_array, dict):
            return dict(list(first_array.items()) + list(second_array.items()))

        elif isinstance(first_array, set) and isinstance(second_array, set):
            return first_array.union(second_array)

        return False

    @staticmethod
    def is_array(var):

        return isinstance(var, (list, tuple))

    @staticmethod
    def isset(variable):

        return variable in locals() or variable in globals()

    @staticmethod
    def loadJsonFile(name):

        data_path = os.getcwd() + '/valid/{}.json'.format(name)

        with open(data_path, 'r') as read_file:

            return json.load(read_file)

    def test_not_on_platform_returns_correctly(self):

        config = Config()

        self.assertFalse(config.is_valid_platform())

    def test_on_platform_returns_correctly_in_runtime(self):

        config = Config(self.mockEnvironmentDeploy)

        self.assertTrue(config.is_valid_platform())

    def test_on_platform_returns_correctly_in_build(self):

        config = Config(self.mockEnvironmentBuild)

        self.assertTrue(config.in_build())

    def test_inbuild_in_build_phase_is_true(self):

        config = Config(self.mockEnvironmentBuild)

        self.assertTrue(config.in_build())

    def test_inbuild_in_deploy_phase_is_false(self):

        config = Config(self.mockEnvironmentDeploy)

        self.assertFalse(config.in_build())

    def _test_buildtime_properties_are_available(self):

        config = Config(self.mockEnvironmentBuild)

        self.assertEquals('/app', config.appDir)
        self.assertEquals('app', config.applicationName)
        self.assertEquals('test-project', config.project)
        self.assertEquals('abc123', config.treeId)
        self.assertEquals('def789', config.entropy)

    def _test_runtime_properties_are_available(self):

        config = Config(self.mockEnvironmentDeploy)

        self.assertEquals('feature-x', config.branch)
        self.assertEquals('feature-x-hgi456', config.environment)
        self.assertEquals('/app/web', config.docRoot)

    def test_load_routes_in_runtime_works(self):

        config = Config(self.mockEnvironmentDeploy)
        routes = config.routes

        self.assertTrue(self.is_array(routes))

    def test_load_routes_in_build_fails(self):

        config = Config(self.mockEnvironmentBuild)

        self.assertRaises(RuntimeError, config.routes())

    def test_get_route_by_id_works(self):

        config = Config(self.mockEnvironmentDeploy)
        route = config.get_route('main')

        self.assertEquals('https://www.{default}/', route['original_url'])

    def test_get_non_existent_route_throws_exception(self):

        config = Config(self.mockEnvironmentDeploy)

        self.assertRaises(ValueError, config.get_route('missing'))

    def test_onenterprise_returns_true_on_enterprise(self):

        env = self.mockEnvironmentDeploy
        env['PLATFORM_MODE'] = 'enterprise'

        config = Config(env)

        self.assertTrue(config.on_enterprise())

    def test_onenterprise_returns_false_on_standard(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertFalse(config.on_enterprise())

    def test_onproduction_on_enterprise_prod_is_true(self):

        env = self.mockEnvironmentDeploy
        env['PLATFORM_MODE'] = 'enterprise'
        env['PLATFORM_BRANCH'] = 'production'

        config = Config(env)

        self.assertTrue(config.on_production())

    def test_onproduction_on_enterprise_stg_is_false(self):

        env = self.mockEnvironmentDeploy
        env['PLATFORM_MODE'] = 'enterprise'
        env['PLATFORM_BRANCH'] = 'staging'

        config = Config(env)

        self.assertFalse(config.on_production())

    def test_onproduction_on_standard_prod_is_true(self):

        env = self.mockEnvironmentDeploy
        env['PLATFORM_BRANCH'] = 'master'

        config = Config(env)

        self.assertTrue(config.on_production())

    def test_onproduction_on_standard_stg_is_false(self):

        # The fixture has a non-master branch set by default.

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertFalse(config.on_production())

    def test_credentials_existing_relationship_returns(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        creds = config.credentials('database')

        self.assertEquals('mysql', creds['scheme'])
        self.assertEquals('mysql:10.2', creds['type'])

    def test_credentials_missing_relationship_throws(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertRaises(ValueError, config.credentials('does-not-exist'))

    def test_credentials_missing_relationship_index_throws(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertRaises(ValueError, config.credentials('database', 3))

    def test_reading_existing_variable_works(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertEquals('someval', config.variable('somevar'))

    def test_reading_missing_variable_returns_default(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertEquals('default-val', config.variable('missing', 'default-val'))

    def test_variables_returns_on_platform(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        variables = config.variables()

        self.assertEquals('someval', variables['somvar'])

    def test_build_property_in_build_exists(self):

        env = self.mockEnvironmentBuild

        config = Config(env)

        self.assertTrue(self.isset(config.appDir))
        self.assertTrue(self.isset(config.applicationName))
        self.assertTrue(self.isset(config.project))
        self.assertTrue(self.isset(config.treeId))
        self.assertTrue(self.isset(config.entropy))

        self.assertEquals('/app', config.appDir)
        self.assertEquals('app', config.applicationName)
        self.assertEquals('test-project', config.project)
        self.assertEquals('abc123', config.treeId)
        self.assertEquals('def789', config.entropy)

    def test_build_and_deploy_properties_in_deploy_exists(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertTrue(self.isset(config.appDir))
        self.assertTrue(self.isset(config.applicationName))
        self.assertTrue(self.isset(config.project))
        self.assertTrue(self.isset(config.treeId))
        self.assertTrue(self.isset(config.entropy))

        self.assertTrue(self.isset(config.branch))
        self.assertTrue(self.isset(config.environment))
        self.assertTrue(self.isset(config.documentRoot))
        self.assertTrue(self.isset(config.smtpHost))

        self.assertEquals('/app', config.appDir)
        self.assertEquals('app', config.applicationName)
        self.assertEquals('test-project', config.project)
        self.assertEquals('abc123', config.treeId)
        self.assertEquals('def789', config.entropy)

        self.assertEquals('feature-x', config.branch)
        self.assertEquals('feature-x-hgi456', config.environment)
        self.assertEquals('/app/web', config.documentRoot)
        self.assertEquals('1.2.3.4', config.smtpHost)

    def test_deploy_property_in_build_throws(self):

        env = self.mockEnvironmentBuild

        config = Config(env)

        self.assertFalse(self.isset(config.branch))
        self.assertRaises(ValueError, config.branch)

    def test_missing_property_throws_in_build(self):

        env = self.mockEnvironmentBuild

        config = Config(env)

        self.assertFalse(self.isset(config.missing))
        self.assertRaises(ValueError, config.missing)

    def test_missing_property_throws_in_deploy(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        self.assertFalse(self.isset(config.missing))
        self.assertRaises(ValueError, config.missing)

    def test_application_array_available(self):

        env = self.mockEnvironmentDeploy

        config = Config(env)

        app = config.application()

        self.assertEquals('python:3.7', app['type'])

    @staticmethod
    def test_invalid_json_throws():
        """

        :return:

        ..todo:: Figure out format on inputted env variable. Should be a dictionary?
        ..todo:: Figure out how to handle expectException/expectExceptionMessage for JSON decode
        """

        config = Config({'PLATFORM_APPLICATION_NAME': 'app',
                         'PLATFORM_ENVIRONMENT': 'test-environment',
                         'PLATFORM_VARIABLES': base64.b64encode('{some-invalid-json}')})

    def test_custom_prefix_works(self):

        config = Config({'FAKE_APPLICATION_NAME': 'test-application'}, 'FAKE_')

        self.assertTrue(config.is_valid_platform())

    @staticmethod
    def encode(value):

        # return base64.encodestring(json.dumps(value))
        # return json.dumps(value)
        return base64.b64encode(json.dumps(value).encode('utf-8'))
        # return base64.b64encode(json.dumps(value))


if __name__ == "__main__":
    # unittest.main()

    c = ConfigTest()
    c.setUp()
